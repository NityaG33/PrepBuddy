from pathlib import Path

from fastapi import UploadFile


PDF_SIGNATURE = b"%PDF-"


class UploadValidationError(ValueError):
    """Expected validation failure for an uploaded file."""


async def save_pdf_upload(
    upload: UploadFile,
    destination: Path,
    *,
    max_upload_bytes: int,
    read_chunk_bytes: int,
) -> int:
    """Stream an upload to disk, enforcing a size limit and PDF signature.

    The temporary file is removed on every validation or I/O failure, so an
    invalid upload never becomes a visible document in the uploads directory.
    """
    temporary_path = destination.with_suffix(destination.suffix + ".uploading")
    bytes_written = 0
    signature_bytes = b""

    try:
        with temporary_path.open("xb") as output_file:
            while chunk := await upload.read(read_chunk_bytes):
                bytes_written += len(chunk)

                if bytes_written > max_upload_bytes:
                    raise UploadValidationError(
                        "Uploaded PDF exceeds the configured size limit"
                    )

                if len(signature_bytes) < len(PDF_SIGNATURE):
                    signature_bytes += chunk[
                        : len(PDF_SIGNATURE) - len(signature_bytes)
                    ]

                output_file.write(chunk)

        if bytes_written == 0:
            raise UploadValidationError("Uploaded file is empty")

        if not signature_bytes.startswith(PDF_SIGNATURE):
            raise UploadValidationError(
                "Uploaded file does not have a valid PDF signature"
            )

        temporary_path.replace(destination)

        return bytes_written

    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()

        raise

    finally:
        await upload.close()
