from services.hash_service import calculate_file_hash


def test_same_file_produces_same_hash(tmp_path):
    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"Sample PDF content")

    first_hash = calculate_file_hash(str(file_path))
    second_hash = calculate_file_hash(str(file_path))

    assert first_hash == second_hash


def test_different_files_produce_different_hashes(tmp_path):
    file_one = tmp_path / "file_one.pdf"
    file_two = tmp_path / "file_two.pdf"

    file_one.write_bytes(b"Content one")
    file_two.write_bytes(b"Content two")

    hash_one = calculate_file_hash(str(file_one))
    hash_two = calculate_file_hash(str(file_two))

    assert hash_one != hash_two


def test_hash_is_sha256_hexadecimal(tmp_path):
    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"Sample PDF content")

    file_hash = calculate_file_hash(str(file_path))

    assert len(file_hash) == 64
    assert all(char in "0123456789abcdef" for char in file_hash)