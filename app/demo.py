"""Seed and demo module for Offline Ofrenda Keeper.

Provides instant loading of the fictional 'Abuela Rosa' demo ofrenda
with pre-populated memories, offerings, portrait, AI remembrance,
and local voice recreation for seamless offline hackathon evaluations.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional

from app.schemas import OfrendaRecord, VoiceConsentRecord
from app.storage import Storage
from app.voice import get_voice_service
from app.voice.watermark import stamp_wav_provenance

DEMO_OFRENDA_ID = "00000000-0000-4000-8000-000000000001"

# Minimal dignified 1x1 valid PNG
SAMPLE_PHOTO_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff"
    b"?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
)


def seed_demo_ofrenda(storage: Optional[Storage] = None) -> OfrendaRecord:
    """Create or reset the fictional 'Abuela Rosa' demo ofrenda on disk."""
    store = storage or Storage()
    folder = store.get_folder(DEMO_OFRENDA_ID)
    folder.mkdir(parents=True, exist_ok=True)

    # 1. Save portrait photo
    photo_file = folder / "photo.png"
    photo_file.write_bytes(SAMPLE_PHOTO_BYTES)

    remembrance_text = (
        "Rosa Hernández es recordada con infinito amor por toda su familia. Su hogar siempre estuvo impregnado "
        "del dulce aroma del pan de muerto recién horneado, los tamales de mole y el reconfortante café de olla. "
        "Cada rincón guardaba el eco de su risa y de canciones entrañables como Cielito Lindo y Amor Eterno, "
        "que llenaban de alegría las tardes familiares. Su rosario de plata y sus agujas de tejer permanecen como "
        "testimonios silenciosos de sus manos generosas y su corazón paciente. Este altar rinde homenaje a su vida "
        "luminosa y mantiene encendida la llama de su memoria."
    )

    story_text = (
        "Abuela Rosa nos enseñó que la cocina es el corazón del hogar. Cada diciembre nos reuníamos "
        "todos para preparar tamales juntos, mientras ella cantaba y contaba historias de su juventud."
    )

    transcript = (
        "Recuerdo cuando nos decía: 'La vida se celebra con amor, con música y compartiendo lo que "
        "tenemos en la mesa'."
    )

    record = OfrendaRecord(
        id=DEMO_OFRENDA_ID,
        created_at=datetime.now(timezone.utc).isoformat(),
        name="Rosa Hernandez",
        relationship="Abuela",
        birth_year=1941,
        death_year=2023,
        language="es",
        foods=["tamales de mole", "arroz con leche", "pan de muerto", "mole negro"],
        drinks=["café de olla", "atole de vainilla"],
        songs=["Cielito Lindo", "Amor Eterno"],
        objects=["su rosario de plata", "agujas de tejer", "rebozo bordado"],
        story_text=story_text,
        transcript=transcript,
        photo="photo.png",
        remembrance=remembrance_text,
        generated_by="ollama:llama3.2:3b",
        model_used="llama3.2:3b",
    )

    # Save ofrenda.json
    json_path = folder / "ofrenda.json"
    json_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    # 2. Seed Voice Reference and Synthetic Remembrance Voice
    try:
        voice_service = get_voice_service()
        engine = voice_service.get_active_engine()

        voice_folder = store.get_voice_folder(DEMO_OFRENDA_ID)
        ref_path = voice_folder / "reference_audio.wav"

        # Generate a warm reference audio file
        engine.synthesize(
            text="Grabación de voz familiar para memoria y recuerdo de Rosa Hernández.",
            reference_audio_path=ref_path,
            output_path=ref_path,
            language="es",
        )

        consent = VoiceConsentRecord(
            authorized_by="María Hernández (Hija)",
            confirmed_permission=True,
        )

        store.save_voice_reference(
            ofrenda_id=DEMO_OFRENDA_ID,
            audio_bytes=ref_path.read_bytes(),
            ext="wav",
            consent=consent,
            duration_s=3.5,
        )

        # Synthesize remembrance voice
        synth_out = voice_folder / "remembrance_synthesized.wav"
        duration_s = engine.synthesize(
            text=remembrance_text,
            reference_audio_path=ref_path,
            output_path=synth_out,
            language="es",
        )

        watermarked_wav = stamp_wav_provenance(
            synth_out.read_bytes(),
            authorized_by="María Hernández (Hija)",
            deceased_name="Rosa Hernandez",
            model_name=engine.name,
        )

        record = store.save_synthesized_voice(
            ofrenda_id=DEMO_OFRENDA_ID,
            wav_bytes=watermarked_wav,
            model_used=engine.name,
            language="es",
            duration_s=duration_s,
        )
    except Exception:
        pass

    return record
