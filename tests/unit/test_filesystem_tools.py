"""Unit tests for filesystem tools."""

import os
import tempfile

import pytest

from actra.tools.filesystem import (
    find_file,
    list_directory,
    create_folder,
    create_file,
    copy_file,
    move_file,
    delete_file,
)


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestFindFile:
    def test_find_existing_file(self, tmp_dir):
        # Create a test file
        test_file = os.path.join(tmp_dir, "test_document.txt")
        open(test_file, "w").close()

        result = find_file(tmp_dir, "*.txt")
        assert result.success is True
        assert len(result.data["matches"]) == 1
        assert "test_document.txt" in result.data["matches"][0]

    def test_find_no_matches(self, tmp_dir):
        result = find_file(tmp_dir, "*.xyz")
        assert result.success is True
        assert len(result.data["matches"]) == 0

    def test_find_in_nonexistent_dir(self):
        result = find_file("/nonexistent/path/12345", "*.txt")
        assert result.success is False
        assert result.error.code == "NOT_FOUND"


class TestListDirectory:
    def test_list_contents(self, tmp_dir):
        # Create some items
        open(os.path.join(tmp_dir, "file.txt"), "w").close()
        os.mkdir(os.path.join(tmp_dir, "subdir"))

        result = list_directory(tmp_dir)
        assert result.success is True
        names = [c["name"] for c in result.data["contents"]]
        assert "file.txt" in names
        assert "subdir" in names

    def test_list_nonexistent(self):
        result = list_directory("/nonexistent/path/12345")
        assert result.success is False


class TestCreateFolder:
    def test_create_new_folder(self, tmp_dir):
        path = os.path.join(tmp_dir, "new_folder")
        result = create_folder(path)
        assert result.success is True
        assert os.path.isdir(path)

    def test_create_existing_folder(self, tmp_dir):
        # Should succeed silently (exist_ok=True)
        result = create_folder(tmp_dir)
        assert result.success is True

    def test_create_nested_folders(self, tmp_dir):
        path = os.path.join(tmp_dir, "a", "b", "c")
        result = create_folder(path)
        assert result.success is True
        assert os.path.isdir(path)


class TestCreateFile:
    def test_create_file_with_content(self, tmp_dir):
        path = os.path.join(tmp_dir, "hello.txt")
        result = create_file(path, content="Hello, World!")
        assert result.success is True
        assert os.path.isfile(path)
        assert open(path).read() == "Hello, World!"

    def test_create_empty_file(self, tmp_dir):
        path = os.path.join(tmp_dir, "empty.txt")
        result = create_file(path)
        assert result.success is True
        assert os.path.isfile(path)


class TestCopyFile:
    def test_copy_file(self, tmp_dir):
        src = os.path.join(tmp_dir, "original.txt")
        dst = os.path.join(tmp_dir, "copy.txt")
        open(src, "w").write("data")

        result = copy_file(src, dst)
        assert result.success is True
        assert os.path.isfile(dst)
        assert open(dst).read() == "data"

    def test_copy_destination_exists_without_overwrite_fails(self, tmp_dir):
        src = os.path.join(tmp_dir, "src.txt")
        dst = os.path.join(tmp_dir, "dst.txt")
        open(src, "w").write("source data")
        open(dst, "w").write("existing data")

        result = copy_file(src, dst, overwrite=False)
        assert result.success is False
        assert result.error.code == "ALREADY_EXISTS"
        assert open(dst).read() == "existing data"

    def test_copy_destination_exists_with_overwrite_succeeds(self, tmp_dir):
        src = os.path.join(tmp_dir, "src.txt")
        dst = os.path.join(tmp_dir, "dst.txt")
        open(src, "w").write("new source data")
        open(dst, "w").write("old data")

        result = copy_file(src, dst, overwrite=True)
        assert result.success is True
        assert open(dst).read() == "new source data"

    def test_copy_nonexistent(self, tmp_dir):
        result = copy_file("/nonexistent/file.txt", os.path.join(tmp_dir, "dst.txt"))
        assert result.success is False


class TestMoveFile:
    def test_move_file(self, tmp_dir):
        src = os.path.join(tmp_dir, "source.txt")
        dst = os.path.join(tmp_dir, "moved.txt")
        open(src, "w").write("content")

        result = move_file(src, dst)
        assert result.success is True
        assert not os.path.exists(src)
        assert os.path.isfile(dst)

    def test_move_destination_exists_without_overwrite_fails(self, tmp_dir):
        src = os.path.join(tmp_dir, "src.txt")
        dst = os.path.join(tmp_dir, "dst.txt")
        open(src, "w").write("source content")
        open(dst, "w").write("existing content")

        result = move_file(src, dst, overwrite=False)
        assert result.success is False
        assert result.error.code == "ALREADY_EXISTS"
        assert os.path.exists(src)
        assert open(dst).read() == "existing content"

    def test_move_destination_exists_with_overwrite_succeeds(self, tmp_dir):
        src = os.path.join(tmp_dir, "src.txt")
        dst = os.path.join(tmp_dir, "dst.txt")
        open(src, "w").write("new content")
        open(dst, "w").write("old content")

        result = move_file(src, dst, overwrite=True)
        assert result.success is True
        assert not os.path.exists(src)
        assert open(dst).read() == "new content"

    def test_move_nonexistent(self, tmp_dir):
        result = move_file("/nonexistent/file.txt", os.path.join(tmp_dir, "dst.txt"))
        assert result.success is False


class TestDeleteFile:
    def test_delete_file(self, tmp_dir):
        path = os.path.join(tmp_dir, "to_delete.txt")
        open(path, "w").close()

        result = delete_file(path)
        assert result.success is True
        assert not os.path.exists(path)

    def test_delete_nonexistent(self):
        result = delete_file("/nonexistent/file_12345.txt")
        assert result.success is False
        assert result.error.code == "NOT_FOUND"


class TestReadWriteFile:
    def test_read_and_write_file(self, tmp_dir):
        from actra.tools.filesystem import read_file, write_file
        path = os.path.join(tmp_dir, "test_doc.txt")
        w_res = write_file(path, "Hello Actra Security")
        assert w_res.success is True
        assert os.path.exists(path)

        r_res = read_file(path)
        assert r_res.success is True
        assert r_res.data["content"] == "Hello Actra Security"

