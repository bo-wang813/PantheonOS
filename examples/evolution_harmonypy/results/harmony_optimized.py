# File: harmony.py
# harmonypy - A data alignment algorithm.
# Copyright (C) 2018  Ilya Korsunsky
#               2019  Kamil Slowikowski <kslowikowski@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pandas as pd
import numpy as np
import torch
from sklearn.cluster import KMeans
import logging

# create logger
logger = logging.getLogger('harmonypy')
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def get_device(device=None):
    """Get the appropriate device for PyTorch operations."""
    if device is not None:
        return torch.device(device)

    # Check for available accelerators
    if torch.cuda.is_available():
        return torch.device('cuda')
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return torch.device('mps')
    else:
        return torch.device('cpu')


def run_harmony(
    data_mat: np.ndarray,
    meta_data: pd.DataFrame,
    vars_use,
    theta=None,
    lamb=None,
    sigma=0.1,
    nclust=None,
    tau=0,
    block_size=0.05,
    max_iter_harmony=10,
    max_iter_kmeans=20,
    epsilon_cluster=1e-5,
    epsilon_harmony=1e-4,
    alpha=0.2,
    verbose=True,
    random_state=0,
    device=None
):
    """Run Harmony batch effect correction.

    This is a PyTorch implementation matching the R package formulas.
    Supports CPU and GPU (CUDA, MPS) acceleration.

    Parameters
    ----------
    data_mat : np.ndarray
        PCA embedding matrix (cells x PCs or PCs x cells)
    meta_data : pd.DataFrame
        Metadata with batch variables (cells x variables)
    vars_use : str or list
        Column name(s) in meta_data to use for batch correction
    theta : float or list, optional
        Diversity penalty parameter(s). Default is 2 for each batch.
    lamb : float or list, optional
        Ridge regression penalty. Default is 1 for each batch.
        If -1, lambda is estimated automatically (matches R package).
    sigma : float, optional
        Kernel bandwidth for soft clustering. Default is 0.1.
    nclust : int, optional
        Number of clusters. Default is min(N/30, 100).
    tau : float, optional
        Protection against overcorrection. Default is 0.
    block_size : float, optional
        Proportion of cells to update in each block. Default is 0.05.
    max_iter_harmony : int, optional
        Maximum Harmony iterations. Default is 10.
    max_iter_kmeans : int, optional
        Maximum k-means iterations per Harmony iteration. Default is 20.
    epsilon_cluster : float, optional
        K-means convergence threshold. Default is 1e-5.
    epsilon_harmony : float, optional
        Harmony convergence threshold. Default is 1e-4.
    alpha : float, optional
        Alpha parameter for lambda estimation (when lamb=-1). Default is 0.2.
    verbose : bool, optional
        Print progress messages. Default is True.
    random_state : int, optional
        Random seed for reproducibility. Default is 0.
    device : str, optional
        Device to use ('cpu', 'cuda', 'mps'). Default is auto-detect.

    Returns
    -------
    Harmony
        Harmony object with corrected data in Z_corr attribute.
    """
    N = meta_data.shape[0]
    if data_mat.shape[1] != N:
        data_mat = data_mat.T

    assert data_mat.shape[1] == N, \
       "data_mat and meta_data do not have the same number of cells"

    if nclust is None:
        nclust = int(min(round(N / 30.0), 100))

    if isinstance(sigma, float) and nclust > 1:
        sigma = np.repeat(sigma, nclust)

    if isinstance(vars_use, str):
        vars_use = [vars_use]

    # Create batch indicator matrix (one-hot encoded)
    phi = pd.get_dummies(meta_data[vars_use]).to_numpy().T.astype(np.float32)
    phi_n = meta_data[vars_use].describe().loc['unique'].to_numpy().astype(int)

    # Theta handling - default is 2 (matches R package)
    if theta is None:
        theta = np.repeat([2] * len(phi_n), phi_n).astype(np.float32)
    elif isinstance(theta, (float, int)):
        theta = np.repeat([theta] * len(phi_n), phi_n).astype(np.float32)
    elif len(theta) == len(phi_n):
        theta = np.repeat([theta], phi_n).astype(np.float32)
    else:
        theta = np.asarray(theta, dtype=np.float32)

    assert len(theta) == np.sum(phi_n), \
        "each batch variable must have a theta"

    # Lambda handling (matches R package)
    lambda_estimation = False
    if lamb is None:
        lamb = np.repeat([1] * len(phi_n), phi_n).astype(np.float32)
        lamb = np.insert(lamb, 0, 0).astype(np.float32)
    elif lamb == -1:
        lambda_estimation = True
        lamb = np.zeros(1, dtype=np.float32)
    elif isinstance(lamb, (float, int)):
        lamb = np.repeat([lamb] * len(phi_n), phi_n).astype(np.float32)
        lamb = np.insert(lamb, 0, 0).astype(np.float32)
    elif len(lamb) == len(phi_n):
        lamb = np.repeat([lamb], phi_n).astype(np.float32)
        lamb = np.insert(lamb, 0, 0).astype(np.float32)
    else:
        lamb = np.asarray(lamb, dtype=np.float32)
        if len(lamb) == np.sum(phi_n):
            lamb = np.insert(lamb, 0, 0).astype(np.float32)

    # Number of items in each category
    N_b = phi.sum(axis=1)
    Pr_b = (N_b / N).astype(np.float32)

    if tau > 0:
        theta = theta * (1 - np.exp(-(N_b / (nclust * tau)) ** 2))

    # Get device
    device_obj = get_device(device)

    if verbose:
        logger.info(f"Running Harmony (PyTorch on {device_obj})")
        logger.info("  Parameters:")
        logger.info(f"    max_iter_harmony: {max_iter_harmony}")
        logger.info(f"    max_iter_kmeans: {max_iter_kmeans}")
        logger.info(f"    epsilon_cluster: {epsilon_cluster}")
        logger.info(f"    epsilon_harmony: {epsilon_harmony}")
        logger.info(f"    nclust: {nclust}")
        logger.info(f"    block_size: {block_size}")
        if lambda_estimation:
            logger.info(f"    lamb: dynamic (alpha={alpha})")
        else:
            logger.info(f"    lamb: {lamb[1:]}")
        logger.info(f"    theta: {theta}")
        logger.info(f"    sigma: {sigma[:5]}..." if len(sigma) > 5 else f"    sigma: {sigma}")
        logger.info(f"    verbose: {verbose}")
        logger.info(f"    random_state: {random_state}")
        logger.info(f"  Data: {data_mat.shape[0]} PCs Ã— {N} cells")
        logger.info(f"  Batch variables: {vars_use}")

    # Set random seeds
    np.random.seed(random_state)
    torch.manual_seed(random_state)

    # Ensure data_mat is a proper numpy array
    if hasattr(data_mat, 'values'):
        data_mat = data_mat.values
    data_mat = np.asarray(data_mat, dtype=np.float32)

    ho = Harmony(
        data_mat, phi, Pr_b, sigma.astype(np.float32),
        theta, lamb, alpha, lambda_estimation,
        max_iter_harmony, max_iter_kmeans,
        epsilon_cluster, epsilon_harmony, nclust, block_size, verbose,
        random_state, device_obj
    )

    return ho


class Harmony:
    """Harmony class for batch effect correction using PyTorch.

    Supports CPU and GPU acceleration.
    """

    def __init__(
            self, Z, Phi, Pr_b, sigma, theta, lamb, alpha, lambda_estimation,
            max_iter_harmony, max_iter_kmeans,
            epsilon_kmeans, epsilon_harmony, K, block_size, verbose,
            random_state, device
    ):
        self.device = device

        # Convert to PyTorch tensors on device
        # Store with underscore prefix internally, expose as properties returning NumPy arrays
        self._Z_corr = torch.tensor(Z, dtype=torch.float32, device=device)
        self._Z_orig = torch.tensor(Z, dtype=torch.float32, device=device)

        # Simple L2 normalization (with numerical stability)
        den = torch.linalg.norm(self._Z_orig, ord=2, dim=0).clamp_min(1e-8)
        self._Z_cos = self._Z_orig / den

        # Batch indicators
        self._Phi = torch.tensor(Phi, dtype=torch.float32, device=device)
        self._Pr_b = torch.tensor(Pr_b, dtype=torch.float32, device=device)

        self.N = self._Z_corr.shape[1]
        self.B = Phi.shape[0]
        self.d = self._Z_corr.shape[0]

        # Build batch index (cell indices per batch) for fast batch-wise GEMMs.
        # Valid because Phi is one-hot encoded via get_dummies.
        self._batch_index = []
        for b in range(self.B):
            idx = torch.where(self._Phi[b, :] > 0)[0]
            self._batch_index.append(idx)

        # Create Phi_moe with intercept
        ones = torch.ones(1, self.N, dtype=torch.float32, device=device)
        self._Phi_moe = torch.cat([ones, self._Phi], dim=0)

        self.window_size = 3
        self.epsilon_kmeans = epsilon_kmeans
        self.epsilon_harmony = epsilon_harmony

        self._lamb = torch.tensor(lamb, dtype=torch.float32, device=device)
        self.alpha = alpha
        self.lambda_estimation = lambda_estimation
        self._sigma = torch.tensor(sigma, dtype=torch.float32, device=device)
        self.block_size = block_size
        self.K = K
        self.max_iter_harmony = max_iter_harmony
        self.max_iter_kmeans = max_iter_kmeans
        self.verbose = verbose
        self._theta = torch.tensor(theta, dtype=torch.float32, device=device)

        # Precompute per-cell batch index for faster indexing operations.
        # Valid because Phi is one-hot encoded via get_dummies.
        self._batch_id = torch.argmax(self._Phi, dim=0).to(torch.long)  # (N,)
        self._theta_cell = self._theta[self._batch_id]                 # (N,)

        # Rebuild batch index from batch_id (kept for batch-wise GEMMs; B is small)
        self._batch_index = []
        for b in range(self.B):
            self._batch_index.append(torch.where(self._batch_id == b)[0])

        self.objective_harmony = []
        self.objective_kmeans = []
        self.objective_kmeans_dist = []
        self.objective_kmeans_entropy = []
        self.objective_kmeans_cross = []
        self.kmeans_rounds = []

        # Harmony iteration counter (for annealing schedules)
        self._iter_harmony = 0

        self.allocate_buffers()
        self.init_cluster(random_state)
        self.harmonize(self.max_iter_harmony, self.verbose)

    # =========================================================================
    # Properties - Return NumPy arrays for inspection and tutorials
    # =========================================================================

    @property
    def Z_corr(self):
        """Corrected embedding matrix (N x d). Batch effects removed."""
        return self._Z_corr.cpu().numpy().T

    @property
    def Z_orig(self):
        """Original embedding matrix (N x d). Input data before correction."""
        return self._Z_orig.cpu().numpy().T

    @property
    def Z_cos(self):
        """L2-normalized embedding matrix (N x d). Used for clustering."""
        return self._Z_cos.cpu().numpy().T

    @property
    def R(self):
        """Soft cluster assignment matrix (N x K). R[i,k] = P(cell i in cluster k)."""
        return self._R.cpu().numpy().T

    @property
    def Y(self):
        """Cluster centroids matrix (d x K). Columns are cluster centers."""
        return self._Y.cpu().numpy()

    @property
    def O(self):
        """Observed batch-cluster counts (K x B). O[k,b] = sum of R[k,:] for batch b."""
        return self._O.cpu().numpy()

    @property
    def E(self):
        """Expected batch-cluster counts (K x B). E[k,b] = cluster_size[k] * batch_proportion[b]."""
        return self._E.cpu().numpy()

    @property
    def Phi(self):
        """Batch indicator matrix (N x B). One-hot encoding of batch membership."""
        return self._Phi.cpu().numpy().T

    @property
    def Phi_moe(self):
        """Batch indicator with intercept (N x (B+1)). First column is all ones."""
        return self._Phi_moe.cpu().numpy().T

    @property
    def Pr_b(self):
        """Batch proportions (B,). Pr_b[b] = cells in batch b / total cells."""
        return self._Pr_b.cpu().numpy()

    @property
    def theta(self):
        """Diversity penalty parameters (B,). Higher = more mixing encouraged."""
        return self._theta.cpu().numpy()

    @property
    def sigma(self):
        """Clustering bandwidth parameters (K,). Soft assignment kernel width."""
        return self._sigma.cpu().numpy()

    @property
    def lamb(self):
        """Ridge regression penalty ((B+1),). Regularization for batch correction."""
        return self._lamb.cpu().numpy()

    @property
    def objectives(self):
        """List of objective values for compatibility with evaluator."""
        return self.objective_harmony

    def result(self):
        """Return corrected data as NumPy array."""
        return self._Z_corr.cpu().numpy().T

    def allocate_buffers(self):
        self._scale_dist = torch.zeros((self.K, self.N), dtype=torch.float32, device=self.device)
        self._dist_mat = torch.zeros((self.K, self.N), dtype=torch.float32, device=self.device)
        self._O = torch.zeros((self.K, self.B), dtype=torch.float32, device=self.device)
        self._E = torch.zeros((self.K, self.B), dtype=torch.float32, device=self.device)
        self._W = torch.zeros((self.B + 1, self.d), dtype=torch.float32, device=self.device)
        self._R = torch.zeros((self.K, self.N), dtype=torch.float32, device=self.device)
        self._Y = torch.zeros((self.d, self.K), dtype=torch.float32, device=self.device)

        # Augmented Lagrangian / ADMM-style dual variables for batch-mixing enforcement
        self._U = torch.zeros((self.K, self.B), dtype=torch.float32, device=self.device)
        self._rho = 1.0

        # Buffers to avoid per-iteration allocations
        self._R_prev = torch.empty((self.K, self.N), dtype=torch.float32, device=self.device)

        # Buffers for ridge correction (batched SPD systems)
        self._cov = torch.empty((self.K, self.B + 1, self.B + 1), dtype=torch.float32, device=self.device)
        self._RHS = torch.empty((self.K, self.B + 1, self.d), dtype=torch.float32, device=self.device)

    def init_cluster(self, random_state):
        logger.info("Computing initial centroids with sklearn.KMeans...")
        # KMeans needs CPU numpy array
        Z_cos_np = self._Z_cos.cpu().numpy()
        model = KMeans(n_clusters=self.K, init='k-means++',
                       n_init=1, max_iter=25, random_state=random_state)
        model.fit(Z_cos_np.T)
        self._Y = torch.tensor(model.cluster_centers_.T, dtype=torch.float32, device=self.device)
        logger.info("KMeans initialization complete.")

        # Normalize centroids
        self._Y = self._Y / torch.linalg.norm(self._Y, ord=2, dim=0)

        # Compute distance matrix: dist = 2 * (1 - Y.T @ Z_cos)
        self._dist_mat = 2 * (1 - self._Y.T @ self._Z_cos)

        # Compute R
        self._R = -self._dist_mat / self._sigma[:, None]
        self._R = torch.exp(self._R)
        self._R = self._R / self._R.sum(dim=0)

        # Batch diversity statistics
        self._E = torch.outer(self._R.sum(dim=1), self._Pr_b)
        self._O = self._R @ self._Phi.T

        self.compute_objective()
        self.objective_harmony.append(self.objective_kmeans[-1])

    def compute_objective(self):
        # Normalization constant
        norm_const = 2000.0 / self.N

        # K-means error
        kmeans_error = torch.sum(self._R * self._dist_mat).item()

        # Entropy
        _entropy = torch.sum(safe_entropy_torch(self._R) * self._sigma[:, None]).item()

        # Cross entropy (R package formula) with numerical stability
        # Avoid expensive (KxB) @ (BxN) by selecting per-cell batch via gather.
        R_sigma = self._R * self._sigma[:, None]

        O_clamped = torch.clamp(self._O, min=1e-8)
        E_clamped = torch.clamp(self._E, min=1e-8)
        log_ratio = torch.log((O_clamped + E_clamped) / E_clamped)  # (K x B)

        log_ratio_sel = log_ratio[:, self._batch_id]                           # (K x N)
        _cross_entropy = torch.sum(R_sigma * self._theta_cell.unsqueeze(0) * log_ratio_sel).item()

        # Store with normalization constant
        self.objective_kmeans.append((kmeans_error + _entropy + _cross_entropy) * norm_const)
        self.objective_kmeans_dist.append(kmeans_error * norm_const)
        self.objective_kmeans_entropy.append(_entropy * norm_const)
        self.objective_kmeans_cross.append(_cross_entropy * norm_const)

    def harmonize(self, iter_harmony=10, verbose=True):
        converged = False
        for i in range(1, iter_harmony + 1):
            self._iter_harmony = i

            if verbose:
                logger.info(f"Iteration {i} of {iter_harmony}")

            self.cluster()
            self.moe_correct_ridge()

            converged = self.check_convergence(1)
            if converged:
                if verbose:
                    logger.info(f"Converged after {i} iteration{'s' if i > 1 else ''}")
                break

        if verbose and not converged:
            logger.info("Stopped before convergence")

    def cluster(self):
        rounds = 0
        r_tol = 1e-4
        for i in range(self.max_iter_kmeans):
            self._R_prev.copy_(self._R)

            # Update Y
            self._Y = self._Z_cos @ self._R.T
            self._Y = self._Y / torch.linalg.norm(self._Y, ord=2, dim=0).clamp_min(1e-8)

            # Update distance matrix
            self._dist_mat = 2 * (1 - self._Y.T @ self._Z_cos)

            # Update R
            self.update_R()

            # Compute objective once per iteration
            self.compute_objective()

            # Cheap early stopping on assignment stability
            if i >= 2:
                delta = (self._R - self._R_prev).abs().max().item()
                if delta < r_tol:
                    rounds = i + 1
                    break

            if i > self.window_size:
                if self.check_convergence(0):
                    rounds = i + 1
                    break
            rounds = i + 1

        self.kmeans_rounds.append(rounds)
        self.objective_harmony.append(self.objective_kmeans[-1])

    def update_R(self):
        """Augmented Lagrangian / ADMM-style R update enforcing O¡ÖE.

        We enforce near-constraints O_{k,b} ¡Ö E_{k,b} using an augmented Lagrangian:
          <U, O-E> + (rho/2)||O-E||^2

        With one-hot batch membership, this induces a batch-specific per-cluster
        bias added to each cell's logits.

        Implementation (no API change):
          1) base logits from distances: L0 = -dist/sigma
          2) add mixing correction logits derived from U and residual D=(O-E):
                Delta_{k,i} = -(U_{k,b_i} + rho * D_{k,b_i}) * theta_eff[b_i]
          3) R[:,i] = softmax(L0[:,i] + Delta[:,i])
          4) dual ascent: U <- U + rho*(O-E)
          5) optional rho adaptation for robustness
        """
        eps = 1e-8

        # Annealing schedule scalar s_t in [0, 1] over Harmony iterations
        # (continuation: early iterations weaker mixing pressure)
        if self.max_iter_harmony > 1:
            s_t = float((self._iter_harmony - 1) / (self.max_iter_harmony - 1))
        else:
            s_t = 1.0
        s_t = float(np.clip(s_t, 0.0, 1.0))

        # Effective theta under continuation
        theta_eff = (self._theta * s_t).clamp_min(0.0)  # (B,)

        # Base logits from distance and sigma: L0_{k,i} = -d_{k,i} / sigma_k
        L0 = -self._dist_mat / self._sigma[:, None].clamp_min(eps)  # (K x N)
        L0 = L0 - L0.max(dim=0, keepdim=True).values  # stabilize per cell

        # Current residual D = O - E under previous R (or current buffers)
        # Use clamped values for numerical stability.
        O = self._O.clamp_min(eps)
        E = self._E.clamp_min(eps)
        D = (O - E)  # (K x B)

        # Per-cell batch lookup into dual and residual
        U_sel = self._U[:, self._batch_id]          # (K x N)
        D_sel = D[:, self._batch_id]                # (K x N)
        theta_cell_eff = theta_eff[self._batch_id]  # (N,)

        # Mixing correction logits (negative pushes D toward 0)
        Delta = -(U_sel + self._rho * D_sel) * theta_cell_eff.unsqueeze(0)  # (K x N)

        logits = L0 + Delta
        logits = logits - logits.max(dim=0, keepdim=True).values
        R = torch.softmax(logits, dim=0).clamp_min(eps)

        self._R = R
        self._O = self._R @ self._Phi.T
        self._E = torch.outer(self._R.sum(dim=1), self._Pr_b)

        # Dual ascent update: U <- U + rho*(O - E)
        D_new = (self._O - self._E)
        self._U = self._U + self._rho * D_new

        # Optional rho adaptation: increase if residual stalls; decrease if oscillating
        # (simple, robust heuristic; keeps internal only)
        r_norm = torch.linalg.norm(D_new).item()
        if not hasattr(self, "_r_norm_prev"):
            self._r_norm_prev = r_norm

        # If residual not improving, increase rho (stronger enforcement).
        if self._r_norm_prev > 0 and r_norm > 0.99 * self._r_norm_prev:
            self._rho = min(self._rho * 1.1, 50.0)
        # If residual jumps up sharply, decrease rho (reduce oscillations).
        elif r_norm > 1.5 * max(self._r_norm_prev, 1e-8):
            self._rho = max(self._rho * 0.7, 1e-3)

        self._r_norm_prev = r_norm

    def check_convergence(self, i_type):
        if i_type == 0:
            if len(self.objective_kmeans) <= self.window_size + 1:
                return False

            w = self.window_size
            obj_old = sum(self.objective_kmeans[-w-1:-1])
            obj_new = sum(self.objective_kmeans[-w:])
            return abs(obj_old - obj_new) / abs(obj_old) < self.epsilon_kmeans

        if i_type == 1:
            if len(self.objective_harmony) < 2:
                return False

            obj_old = self.objective_harmony[-2]
            obj_new = self.objective_harmony[-1]
            return (obj_old - obj_new) / abs(obj_old) < self.epsilon_harmony

        return True

    def moe_correct_ridge(self):
        """Hierarchical (tied) per-cluster ridge correction.

        Optimized implementation:
          * builds per-cluster covariances analytically from m_k and O[k,b]
          * forms RHS via batch-wise GEMMs (loop over batches; B is small)
          * solves all clusters at once via batched Cholesky
          * applies correction via batch-wise GEMMs (no loop over clusters)

        Continuation / annealing:
          * scale correction strength early to reduce overcorrection/oscillations
          * lamb_eff = lamb_base * s_t for batch coefficients only (not intercept)
        """
        eps = 1e-8

        # Annealing schedule scalar s_t in [0, 1] over Harmony iterations
        if self.max_iter_harmony > 1:
            s_t = float((self._iter_harmony - 1) / (self.max_iter_harmony - 1))
        else:
            s_t = 1.0
        s_t = float(np.clip(s_t, 0.0, 1.0))

        # Start from original each time (matches Harmony behavior)
        self._Z_corr.copy_(self._Z_orig)

        # Lambda vector
        if self.lambda_estimation:
            cluster_E = (self._Pr_b * float(self.N)).to(self.device)
            lamb_vec = find_lambda_torch(self.alpha, cluster_E, self.device)
        else:
            lamb_vec = self._lamb

        # Apply annealing to batch coefficients only (not intercept)
        lamb_vec = lamb_vec.clone()
        if lamb_vec.numel() > 1:
            lamb_vec[1:] = lamb_vec[1:] * s_t

        # Shrinkage strength gamma (no API change): tie to mean lambda magnitude.
        gamma = float(torch.mean(lamb_vec[1:]).item()) if lamb_vec.numel() > 1 else 1.0
        gamma = max(gamma, 1e-3)

        gamma_vec = torch.full((self.B + 1,), gamma, dtype=torch.float32, device=self.device)
        gamma_vec[0] = 0.0  # do not shrink intercept

        # Build covariances for all clusters analytically from masses and observed counts.
        # cov_k:
        #   [ m_k      O_k^T ]
        #   [ O_k   diag(O_k)]
        m = self._R.sum(dim=1).clamp_min(eps)  # (K,)
        O = self._O.clamp_min(eps)             # (K x B)

        cov = self._cov
        cov.zero_()

        cov[:, 0, 0] = m
        cov[:, 0, 1:] = O
        cov[:, 1:, 0] = O
        diag_idx = torch.arange(self.B, device=self.device)
        cov[:, 1 + diag_idx, 1 + diag_idx] = O

        # Add ridge + shrinkage on diagonal (broadcasted to K)
        cov = cov + torch.diag(lamb_vec + gamma_vec).unsqueeze(0)

        # Build RHS for all clusters: (K, B+1, d)
        RHS = self._RHS
        RHS.zero_()

        # Intercept row: sum_i R[k,i] * Z[:,i]
        RHS[:, 0, :] = self._R @ self._Z_orig.T  # (K x d)

        # Batch rows: for each batch b, sum_{i in batch b} R[k,i] * Z[:,i]
        for b in range(self.B):
            idx = self._batch_index[b]
            if idx.numel() == 0:
                continue
            Rb = self._R[:, idx]        # (K x nb)
            Zb = self._Z_orig[:, idx]   # (d x nb)
            RHS[:, b + 1, :] = Rb @ Zb.T  # (K x d)

        # Batched solve for Wk_all: (K, B+1, d)
        L = torch.linalg.cholesky(cov)
        Wk_all = torch.cholesky_solve(RHS, L)
        Wk_all[:, 0, :] = 0  # do not remove intercept

        # Apply correction via batch-wise GEMMs:
        # for cells in batch b: corr = (Wk_all[:,b+1,:].T @ R[:,idx])
        for b in range(self.B):
            idx = self._batch_index[b]
            if idx.numel() == 0:
                continue
            Wb = Wk_all[:, b + 1, :]    # (K x d)
            Rb = self._R[:, idx]        # (K x nb)
            corr = Wb.T @ Rb            # (d x nb)
            self._Z_corr[:, idx] -= corr

        # Update Z_cos (with numerical stability)
        den = torch.linalg.norm(self._Z_corr, ord=2, dim=0).clamp_min(1e-8)
        self._Z_cos = self._Z_corr / den


def safe_entropy_torch(x):
    """Compute x * log(x), returning 0 where x is 0 or negative."""
    result = x * torch.log(x)
    result = torch.where(torch.isfinite(result), result, torch.zeros_like(result))
    return result


def harmony_pow_torch(A, T):
    """Element-wise power with different exponents per column (vectorized)."""
    A = A.clamp(min=1e-8)
    return torch.exp(torch.log(A) * T.unsqueeze(0))


def find_lambda_torch(alpha, cluster_E, device):
    """Compute dynamic lambda based on cluster expected counts."""
    lamb = torch.zeros(len(cluster_E) + 1, dtype=torch.float32, device=device)
    lamb[1:] = cluster_E * alpha
    return lamb
