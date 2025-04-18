<div align="center">
  <h1> Pantheon </h1>

  <p> A framework for building distributed LLM based multi-agent system. </p>

  <p>
    <a href="https://github.com/aristoteleo/pantheon-agents/actions/workflows/test.yml">
        <img src="https://github.com/aristoteleo/pantheon-agents/actions/workflows/test.yml/badge.svg" alt="Build Status">
    </a>
    <a href="https://pypi.org/project/pantheon-agents/">
      <img src="https://img.shields.io/pypi/v/pantheon-agents.svg" alt="Install with PyPi" />
    </a>
    <a href="https://github.com/aristoteleo/pantheon-agents/blob/master/LICENSE">
      <img src="https://img.shields.io/github/license/aristoteleo/pantheon-agents" alt="MIT license" />
    </a>
  </p>
</div>


**Work In Progress**


## Installation

```bash
pip install pantheon-agents
```

See the [examples](examples) folder for more details.


## TODO

- [x] REPL for meeting and agent
- [x] Reasoning with O1 / Gemini Flash Thinking / Deepseek-R1
- [x] Distributed
  + [x] Tools
  + [x] Agents
    * [x] Support streaming response
- [x] Toolsets
  + [x] Python
  + [x] R
  + [x] Shell
  + [x] Web Browse
  + [ ] Jupyter
  + [ ] RAG
    * [x] VectorRAG
    * [ ] GraphRAG
    * [x] Package Document
    * [ ] PDF(paper)
    * [ ] Code
- [x] Agent team
  + [x] Sequential Team
  + [x] Swarm Team
  + [x] MoA(Mixture-of-Agents) Team
- [x] Memory persistence
- [ ] Report generation
- [x] Vision ability
- [ ] GUI
  + [ ] Web UI
  + [x] Slack
  + [ ] WeChat
- [ ] Documentation

## Start a chatroom and work with it

### Start a chatroom backend server

```bash
git clone https://github.com/aristoteleo/pantheon-agents.git
cd pantheon-agents

pip install -e .
export OPENAI_API_KEY=your_openai_api_key
python -m pantheon.chatroom
```

Then you can see a service id of chatroom, you can copy it for next step.

### Start chatroom web UI

1. Install node: See https://nodejs.org/en/download

2. Install pnpm: See https://pnpm.io/installation#using-npm

3. Start the web UI:

```bash
git clone https://github.com/aristoteleo/pantheon-ui.git
cd pantheon-ui
pnpm install
pnpm run dev
```

4. Open the web UI: http://localhost:5173 then paste the service id to the input box and click "Connect".
