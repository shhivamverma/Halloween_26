"""Audio watermarking and ethical provenance stamping for synthetic speech."""

import io
from pathlib import Path
import struct
from typing import Dict, Optional

WATERMARK_ARTIST = "AI-Generated Voice Recreation"
WATERMARK_TITLE = "Memorial Simulation Reading"
WATERMARK_COMMENT = "Simulated memorial voice recreation. Not spoken by the deceased. For family ofrenda remembrance only."
WATERMARK_SOFTWARE = "Offline Ofrenda Keeper"


def _build_info_subchunk(fourcc: bytes, text: str) -> bytes:
    data = text.encode("utf-8") + b"\x00"
    length = len(data)
    padding = b"\x00" if (length % 2 != 0) else b""
    return fourcc + struct.pack("<I", length) + data + padding


def stamp_wav_provenance(
    wav_bytes: bytes,
    authorized_by: Optional[str] = None,
    deceased_name: Optional[str] = None,
    model_name: Optional[str] = None,
) -> bytes:
    """Stamp RIFF INFO metadata chunk into WAV bytes to certify provenance."""
    if not wav_bytes.startswith(b"RIFF") or len(wav_bytes) < 44:
        return wav_bytes  # Return unchanged if not valid RIFF header

    title = f"AI Remembrance Recreation for {deceased_name}" if deceased_name else WATERMARK_TITLE
    artist = f"Offline Ofrenda Keeper ({WATERMARK_ARTIST})"
    comment = WATERMARK_COMMENT
    if authorized_by:
        comment += f" Authorized by: {authorized_by}."
    software = f"{WATERMARK_SOFTWARE} ({model_name})" if model_name else WATERMARK_SOFTWARE

    info_chunks = [
        _build_info_subchunk(b"IART", artist),
        _build_info_subchunk(b"INAM", title),
        _build_info_subchunk(b"ICMT", comment),
        _build_info_subchunk(b"ISFT", software),
    ]

    info_body = b"INFO" + b"".join(info_chunks)
    list_chunk = b"LIST" + struct.pack("<I", len(info_body)) + info_body

    # Update RIFF size header
    original_riff_size = struct.unpack("<I", wav_bytes[4:8])[0]
    new_riff_size = original_riff_size + len(list_chunk)

    modified_wav = wav_bytes[:4] + struct.pack("<I", new_riff_size) + wav_bytes[8:] + list_chunk
    return modified_wav


# Alias for explicit naming
inject_riff_provenance = stamp_wav_provenance


def read_riff_metadata(wav_bytes: bytes) -> Dict[str, str]:
    """Extract and parse all RIFF INFO subchunks from a WAV file."""
    meta: Dict[str, str] = {}
    if not wav_bytes.startswith(b"RIFF") or len(wav_bytes) < 12:
        return meta

    pos = 12  # Skip 'RIFF' + 4-byte size + 'WAVE'
    file_len = len(wav_bytes)
    while pos + 8 <= file_len:
        chunk_id = wav_bytes[pos : pos + 4]
        chunk_size = struct.unpack("<I", wav_bytes[pos + 4 : pos + 8])[0]
        pos += 8

        if chunk_id == b"LIST" and pos + 4 <= file_len:
            list_type = wav_bytes[pos : pos + 4]
            if list_type == b"INFO":
                info_pos = pos + 4
                info_end = min(pos + chunk_size, file_len)
                while info_pos + 8 <= info_end:
                    sub_id = wav_bytes[info_pos : info_pos + 4].decode("latin1", errors="replace")
                    sub_len = struct.unpack("<I", wav_bytes[info_pos + 4 : info_pos + 8])[0]
                    info_pos += 8
                    sub_data = wav_bytes[info_pos : min(info_pos + sub_len, info_end)]
                    meta[sub_id] = sub_data.rstrip(b"\x00").decode("utf-8", errors="replace")
                    info_pos += sub_len + (sub_len % 2)
        pos += chunk_size + (chunk_size % 2)
    return meta


def inspect_wav_watermark(wav_bytes: bytes) -> Dict[str, str]:
    """Inspect WAV bytes for presence of provenance watermark tags."""
    tags = {}
    if b"LIST" in wav_bytes and b"INFO" in wav_bytes:
        if b"AI-Generated Voice Recreation" in wav_bytes:
            tags["watermark"] = WATERMARK_ARTIST
        if b"Memorial Simulation" in wav_bytes or b"Remembrance Recreation" in wav_bytes:
            tags["type"] = WATERMARK_TITLE
    return tags
