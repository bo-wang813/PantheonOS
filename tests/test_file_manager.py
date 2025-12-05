import os
from tempfile import TemporaryDirectory

from pantheon.toolsets.file_transfer.client import FileTransferClient
from pantheon.toolsets.file_transfer.worker import FileTransferToolSet
from pantheon.toolsets.file_manager import FileManagerToolSet
from pantheon.toolset import run_toolsets
from pantheon.remote import connect_remote


async def test_file_transfer():
    test_file = "test.txt"
    with open(test_file, "w") as f:
        f.write("Hello, world!")

    test_output_file = "test_output.txt"
    with TemporaryDirectory() as temp_dir:
        toolset = FileTransferToolSet("file_transfer", temp_dir)
        async with run_toolsets([toolset], log_level="DEBUG"):
            client = FileTransferClient(toolset.service_id)
            await client.send_file(test_file, "test.txt", chunk_size=10000)
            await client.fetch_file(test_output_file, "test.txt", chunk_size=10000)
            with open(test_output_file, "r") as f:
                assert f.read() == "Hello, world!"

    os.remove(test_file)
    os.remove(test_output_file)


async def test_file_manager():
    with TemporaryDirectory() as temp_dir:
        toolset = FileManagerToolSet("file_manager", temp_dir)
        async with run_toolsets([toolset]):
            service = await connect_remote(toolset.service_id)
            await service.invoke("create_directory", {"sub_dir": "test1"})
            await service.invoke("create_directory", {"sub_dir": "test2"})
            await service.invoke("write_file", {"file_path": "test.txt", "content": "Hello, world!1"})
            await service.invoke("write_file", {"file_path": "test1/test.txt", "content": "Hello, world!2"})
            await service.invoke("write_file", {"file_path": "test2/test.txt", "content": "Hello, world!3"})
            resp = await service.invoke("list_files")
            assert len(resp['files']) == 3
            resp = await service.invoke("read_file", {"file_path": "test.txt"})
            assert resp["content"] == "Hello, world!1"
            resp = await service.invoke("read_file", {"file_path": "test1/test.txt"})
            assert resp["content"] == "Hello, world!2"
            resp = await service.invoke("read_file", {"file_path": "test2/test.txt"})
            assert resp["content"] == "Hello, world!3"
            resp = await service.invoke("delete_path", {"path": "test.txt"})
            assert resp["success"]
            resp = await service.invoke("list_files")
            assert len(resp['files']) == 2
            resp = await service.invoke("delete_path", {"path": "test1", "recursive": True})
            assert resp["success"]
            resp = await service.invoke("list_files")
            assert len(resp['files']) == 1
            resp = await service.invoke("delete_path", {"path": "test2", "recursive": True})
            assert resp["success"]
            resp = await service.invoke("list_files")
            assert len(resp['files']) == 0

            # error cases
            resp = await service.invoke("delete_path", {"path": "test1", "recursive": True})
            assert not resp["success"]
            resp = await service.invoke("delete_path", {"path": "test1/test.txt", "recursive": True})
            assert not resp["success"]
            resp = await service.invoke("delete_path", {"path": "../test.txt"})
            assert not resp["success"]
