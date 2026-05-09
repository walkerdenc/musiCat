from typing import List

import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

from models import (
    DetectedElement, MIDISettings,
    SCALES, ROOT_NOTES,
    SHAPE_DURATIONS, SHAPE_BASE_VELOCITY,
    CHANNEL_OCTAVE_OFFSET, CHANNEL_PROGRAMS, CHANNEL_NAMES,
    COLOR_GROUP_TO_CHANNEL,
)

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _midi_note_name(note: int) -> str:
    octave = note // 12 - 1
    return f"{_NOTE_NAMES[note % 12]}{octave}"


def _snap_to_scale(target: int, scale_intervals: List[int], root_idx: int) -> int:
    """Return the scale note closest to target."""
    scale_set = {n for n in range(128) if (n - root_idx) % 12 in scale_intervals}
    if not scale_set:
        return max(0, min(127, target))
    return min(scale_set, key=lambda n: abs(n - target))


def assign_midi_properties(elements: List[DetectedElement], settings: MIDISettings) -> None:
    """Set midi_channel, midi_note, midi_velocity, note_duration, note_start_tick on each element."""
    scale_intervals = SCALES[settings.scale_name]
    root_idx = ROOT_NOTES.index(settings.root_note_name)
    tpb = settings.ticks_per_beat
    total_ticks = tpb * 4 * settings.bars
    sixteenth = tpb // 4

    for el in elements:
        channel = COLOR_GROUP_TO_CHANNEL[el.color_group]
        el.midi_channel = channel

        # Base MIDI note: root at C4 = 60, shifted by channel octave offset
        base_octave = 4 + CHANNEL_OCTAVE_OFFSET[channel]
        base_midi = (base_octave + 1) * 12 + root_idx

        # Y position (0=top=high, 1=bottom=low) → 2-octave pitch range
        target = base_midi + int((1.0 - el.position[1]) * 24)
        target = max(0, min(127, target))
        note = _snap_to_scale(target, scale_intervals, root_idx)
        el.midi_note = max(0, min(127, note))
        el.note_name = _midi_note_name(el.midi_note)

        # Velocity: shape base ± saturation modifier
        sat_mod = int((el.color_hsv[1] / 255.0 - 0.5) * 30)
        el.midi_velocity = max(40, min(127, SHAPE_BASE_VELOCITY[el.shape] + sat_mod))

        el.note_duration = SHAPE_DURATIONS[el.shape]

        # X position → beat position, quantized to nearest 16th note
        raw_tick = int(el.position[0] * total_ticks)
        el.note_start_tick = (round(raw_tick / sixteenth) * sixteenth) % total_ticks


def generate_midi(
    elements: List[DetectedElement],
    settings: MIDISettings,
    output_path: str,
) -> None:
    """Write a Format-1 MIDI file with one track per active channel."""
    tpb = settings.ticks_per_beat
    mid = MidiFile(type=1, ticks_per_beat=tpb)

    # Tempo / time-signature track
    tempo_track = MidiTrack()
    mid.tracks.append(tempo_track)
    tempo_track.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(settings.bpm), time=0))
    tempo_track.append(MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    tempo_track.append(MetaMessage("end_of_track", time=0))

    for ch in sorted(set(el.midi_channel for el in elements)):
        ch_elements = [el for el in elements if el.midi_channel == ch]
        track = MidiTrack()
        mid.tracks.append(track)
        track.append(MetaMessage("track_name", name=CHANNEL_NAMES.get(ch, f"Ch {ch+1}"), time=0))
        track.append(Message("program_change", channel=ch, program=CHANNEL_PROGRAMS.get(ch, 0), time=0))

        # Build (abs_tick, type, note, velocity) events
        events = []
        for el in ch_elements:
            start = el.note_start_tick
            dur = el.note_duration
            vel = el.midi_velocity
            note = el.midi_note

            # High-texture elements get rhythmic repetitions
            repeats = 1
            if el.texture_variance > 40:
                repeats = max(1, min(4, int(el.texture_variance / 20)))

            rep_dur = max(60, dur // repeats)
            for r in range(repeats):
                t_on = start + r * rep_dur
                t_off = t_on + max(30, rep_dur - 30)
                events.append((t_on, "on", note, vel))
                events.append((t_off, "off", note, 0))

        events.sort(key=lambda e: e[0])

        current_tick = 0
        for abs_tick, kind, note, vel in events:
            delta = abs_tick - current_tick
            current_tick = abs_tick
            if kind == "on":
                track.append(Message("note_on", channel=ch, note=note, velocity=vel, time=delta))
            else:
                track.append(Message("note_off", channel=ch, note=note, velocity=0, time=delta))

        track.append(MetaMessage("end_of_track", time=0))

    mid.save(output_path)
