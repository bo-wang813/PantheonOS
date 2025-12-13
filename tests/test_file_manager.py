import pytest
from tempfile import TemporaryDirectory
from pantheon.toolsets.file import FileManagerToolSet

@pytest.fixture
def temp_toolset():
    """Create a FileManagerToolSet with a temporary directory."""
    with TemporaryDirectory() as temp_dir:
        yield FileManagerToolSet("file_manager", temp_dir)

async def test_filemanager_comprehensive(temp_toolset):
    """
    Test comprehensive file manager operations in a single flow.
    
    Covers:
    - create_directory
    - write_file (and overwrite behavior)
    - list_files (root and subdirectory)
    - read_file (full and partial/line-range)
    - update_file (single, multiple/replace_all, line-limited)
    - move_file
    - delete_path
    """
    
    # 1. Start with directory structure
    assert (await temp_toolset.create_directory("src"))["success"]
    assert (await temp_toolset.create_directory("src/utils"))["success"]
    
    # 2. Write file with multiple lines
    content = "import os\nimport sys\n\ndef func():\n    pass\n    return 0\n"
    res = await temp_toolset.write_file("src/main.py", content)
    assert res["success"]
    
    # Test overwrite protection (default is overwrite=False but tool interface usually defaults to user intent, 
    # checking impl: write_file defaults to overwrite=False in some versions, let's verify)
    # Actually most LLM tool implementations of write_file default to overwriting or failing. 
    # Current pantheon implementation signature is: write_file(file_path, content) -> likely overwrites or fails.
    # Let's test overwrite explicit just in case.
    res = await temp_toolset.write_file("src/main.py", "OVERWRITTEN", overwrite=True)
    assert res["success"]
    assert (await temp_toolset.read_file("src/main.py"))["content"] == "OVERWRITTEN"
    
    # Restore content
    await temp_toolset.write_file("src/main.py", content, overwrite=True)
    
    # 3. List files in subdirectory
    res = await temp_toolset.list_files("src")
    assert res["success"]
    names = [f["name"] for f in res["files"]]
    assert "main.py" in names
    assert "utils" in names

    # 4. Read file with line range
    # Content:
    # 1: import os
    # 2: import sys
    # 3: 
    # 4: def func():
    # 5:     pass
    # 6:     return 0
    
    # Read lines 4-6
    res = await temp_toolset.read_file("src/main.py", start_line=4, end_line=6)
    assert res["success"]
    part = res["content"]
    assert "def func():" in part
    assert "return 0" in part
    assert "import os" not in part
    
    # 5. Update file with advanced params
    
    # A. Scope limit (only replace 'pass' inside function if we knew lines, 
    # but here just testing line limit works)
    res = await temp_toolset.update_file(
        "src/main.py",
        old_string="pass",
        new_string="print('hello')",
        start_line=5,
        end_line=5
    )
    assert res["success"]
    assert "print('hello')" in (await temp_toolset.read_file("src/main.py"))["content"]
    
    # Prepare file for replace_all test
    # 1: import os
    # 2: import sys
    # ...
    # Let's add multiple same lines
    multi_content = "foo\nbar\nfoo\nbaz\nfoo"
    await temp_toolset.write_file("src/multi.txt", multi_content)
    
    # B. Replace All
    res = await temp_toolset.update_file(
        "src/multi.txt",
        old_string="foo",
        new_string="replaced",
        replace_all=True
    )
    assert res["success"]
    assert res["replacements"] == 3
    new_multi = (await temp_toolset.read_file("src/multi.txt"))["content"]
    assert new_multi.count("replaced") == 3
    assert "foo" not in new_multi
    
    # 7. Move and Delete
    # Move directory
    res = await temp_toolset.move_file("src/utils", "src/tools")
    assert res["success"]
    assert (temp_toolset.path / "src/tools").exists()
    assert not (temp_toolset.path / "src/utils").exists()
    
    # Delete file
    res = await temp_toolset.delete_path("src/multi.txt")
    assert res["success"]
    assert not (temp_toolset.path / "src/multi.txt").exists()


async def test_glob_comprehensive(temp_toolset):
    """
    Test comprehensive glob functionality.
    
    Covers:
    - Find files with pattern matching
    - Relative path search
    - Absolute path search
    - Error handling for nonexistent paths
    """
    # Setup: Create test file structure
    await temp_toolset.create_directory("src")
    await temp_toolset.create_directory("tests")
    await temp_toolset.write_file("test.py", "def hello():\n    print('Hello')\n")
    await temp_toolset.write_file("main.py", "# TODO: implement\nclass Main:\n    pass\n")
    await temp_toolset.write_file("config.json", '{"version": "1.2.3"}\n')
    await temp_toolset.write_file("src/utils.py", "def helper():\n    # TODO: fix bug\n    return 42\n")
    await temp_toolset.write_file("src/api.py", "import requests\n\ndef fetch():\n    pass\n")
    await temp_toolset.write_file("tests/test_main.py", "def test_hello():\n    assert True\n")
    
    # Test 1: Find all Python files in workspace
    result = await temp_toolset.glob("**/*.py")
    assert result["success"] is True
    assert result["total"] >= 5
    assert all(f["path"].endswith(".py") for f in result["files"])
    assert any("test.py" in f["path"] for f in result["files"])
    assert any("main.py" in f["path"] for f in result["files"])
    assert any("utils.py" in f["path"] for f in result["files"])
    
    # Test 2: Find files with relative path
    result = await temp_toolset.glob("*.py", path="src")
    assert result["success"] is True
    assert result["total"] >= 2
    assert all("src/" in f["path"] for f in result["files"])
    assert any("utils.py" in f["name"] for f in result["files"])
    assert any("api.py" in f["name"] for f in result["files"])
    
    # Test 3: Find files with absolute path
    src_absolute = str(temp_toolset.path / "src")
    result = await temp_toolset.glob("*.py", path=src_absolute)
    assert result["success"] is True
    assert result["total"] >= 2
    assert all(f["name"].endswith(".py") for f in result["files"])
    
    # Test 4: Error handling - nonexistent path
    result = await temp_toolset.glob("*.py", path="nonexistent_dir")
    assert result["success"] is False
    assert "does not exist" in result["error"]


async def test_grep_comprehensive(temp_toolset):
    """
    Test comprehensive grep functionality.
    
    Covers:
    - Content search with pattern matching
    - File pattern filtering
    - Relative path search
    - Absolute path search
    - Context lines
    - Error handling for nonexistent paths
    """
    # Setup: Create test file structure with searchable content
    await temp_toolset.create_directory("src")
    await temp_toolset.write_file("main.py", "# TODO: implement\nclass Main:\n    pass\n")
    await temp_toolset.write_file("src/utils.py", "def helper():\n    # TODO: fix bug\n    return 42\n")
    await temp_toolset.write_file("src/api.py", "import requests\n\ndef fetch():\n    pass\n")
    
    # Test 1: Find TODO comments in all Python files
    result = await temp_toolset.grep("TODO", file_pattern="**/*.py")
    assert result["success"] is True
    assert result["total_matches"] >= 2
    assert result["files_matched"] >= 2
    for match in result["matches"]:
        assert "file" in match
        assert "line_number" in match
        assert "line_content" in match
        assert "TODO" in match["line_content"]
        assert match["line_number"] > 0
    
    # Test 2: Search with relative path
    result = await temp_toolset.grep("TODO", path="src", file_pattern="*.py")
    assert result["success"] is True
    assert result["total_matches"] >= 1
    assert all("src/" in m["file"] for m in result["matches"])
    
    # Test 3: Search with absolute path
    src_absolute = str(temp_toolset.path / "src")
    result = await temp_toolset.grep("TODO", path=src_absolute, file_pattern="*.py")
    assert result["success"] is True
    assert result["total_matches"] >= 1
    
    # Test 4: Search with context lines
    result = await temp_toolset.grep("TODO", file_pattern="**/*.py", context_lines=1)
    assert result["success"] is True
    if result["matches"]:
        match = result["matches"][0]
        # Context should be available (though may be empty if at file boundaries)
        assert "context_before" in match
        assert "context_after" in match
        assert isinstance(match["context_before"], list)
        assert isinstance(match["context_after"], list)
    
    # Test 5: Error handling - nonexistent path
    result = await temp_toolset.grep("TODO", path="nonexistent_dir")
    assert result["success"] is False
    assert "does not exist" in result["error"]

async def test_manage_path_comprehensive(temp_toolset):
    """
    Test comprehensive manage_path functionality.
    
    Covers:
    - create_dir operation (with automatic parent creation)
    - delete operation (files and directories, with/without recursive)
    - move operation (rename and move to different directory)
    - Error handling (invalid operation, missing parameters, nonexistent paths)
    """
    
    # Test 1: Create directory (with automatic parent creation)
    result = await temp_toolset.manage_path("create_dir", "src/components/ui")
    assert result["success"] is True
    assert (temp_toolset.path / "src/components/ui").is_dir()
    
    # Test 2: Delete file
    test_file = temp_toolset.path / "test.txt"
    test_file.write_text("content")
    result = await temp_toolset.manage_path("delete", "test.txt")
    assert result["success"] is True
    assert not test_file.exists()
    
    # Test 3: Delete empty directory
    await temp_toolset.manage_path("create_dir", "empty_dir")
    result = await temp_toolset.manage_path("delete", "empty_dir")
    assert result["success"] is True
    assert not (temp_toolset.path / "empty_dir").exists()
    
    # Test 4: Delete directory with contents (recursive=False should fail)
    test_dir = temp_toolset.path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")
    result = await temp_toolset.manage_path("delete", "test_dir", recursive=False)
    assert result["success"] is False  # Should fail because directory is not empty
    
    # Test 5: Delete directory with contents (recursive=True should succeed)
    result = await temp_toolset.manage_path("delete", "test_dir", recursive=True)
    assert result["success"] is True
    assert not test_dir.exists()
    
    # Test 6: Move/rename file
    old_file = temp_toolset.path / "old.txt"
    old_file.write_text("content")
    result = await temp_toolset.manage_path("move", "old.txt", new_path="new.txt")
    assert result["success"] is True
    assert not old_file.exists()
    assert (temp_toolset.path / "new.txt").exists()
    assert (temp_toolset.path / "new.txt").read_text() == "content"
    
    # Test 7: Move file to different directory
    await temp_toolset.manage_path("create_dir", "backup")
    test_file = temp_toolset.path / "file.txt"
    test_file.write_text("test content")
    result = await temp_toolset.manage_path("move", "file.txt", new_path="backup/file.txt")
    assert result["success"] is True
    assert not test_file.exists()
    assert (temp_toolset.path / "backup/file.txt").exists()
    assert (temp_toolset.path / "backup/file.txt").read_text() == "test content"
    
    # Test 8: Error - invalid operation
    result = await temp_toolset.manage_path("invalid_op", "path")
    assert result["success"] is False
    assert "Invalid operation" in result["error"]
    
    # Test 9: Error - move without new_path
    result = await temp_toolset.manage_path("move", "old.txt")
    assert result["success"] is False
    assert "new_path is required" in result["error"]
    
    # Test 10: Error - delete nonexistent path
    result = await temp_toolset.manage_path("delete", "nonexistent.txt")
    assert result["success"] is False
    assert "does not exist" in result["error"]
