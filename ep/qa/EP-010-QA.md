# EP-010 "ELECTRO EP" — QA EVIDENCE (raw values, generated)

Rendered 10/10. Gate: PASS.

| # | Track | BPM | File | Bytes | Duration (s) | LUFS | True Peak (dBTP) | SHA256 (first 16) |
|---|-------|-----|------|-------|--------------|------|------------------|-------------------|
| 01 | Neon Voltage | 168 | mp3/neon-voltage.mp3 | 5490369 | 137.232 | -14.01 | -8.53 | 78d2679031d72650 |
| 02 | Circuit Breaker | 150 | mp3/circuit-breaker.mp3 | 5382852 | 134.544 | -14.0 | -8.06 | 862841a72f250e73 |
| 03 | Midnight Protocol | 134 | mp3/midnight-protocol.mp3 | 5448134 | 136.176 | -14.0 | -8.3 | 05cf31b03f06c4ae |
| 04 | Chrome Hearts | 172 | mp3/chrome-hearts.mp3 | 5359810 | 133.968 | -14.01 | -8.61 | 3bc67cfa80e69c46 |
| 05 | Voltage Drop | 128 | mp3/voltage-drop.mp3 | 5403969 | 135.072 | -14.0 | -8.15 | 2fdece1b5d5ec41c |
| 06 | Static Bloom | 144 | mp3/static-bloom.mp3 | 5337729 | 133.416 | -14.0 | -8.37 | b6512a27de777a34 |
| 07 | Pulse Reactor | 178 | mp3/pulse-reactor.mp3 | 5398210 | 134.928 | -14.01 | -8.7 | 2700c200bc0a6b4e |
| 08 | Afterglow Drive | 138 | mp3/afterglow-drive.mp3 | 5289732 | 132.216 | -14.0 | -8.18 | f3b4d50be2b05783 |
| 09 | Overdrive | 164 | mp3/overdrive.mp3 | 5386686 | 134.64 | -14.0 | -8.29 | f992d5f27a41be19 |
| 10 | Aurora Circuit | 156 | mp3/aurora-circuit.mp3 | 5420291 | 135.48 | -14.01 | -8.82 | 85ca7077d5221229 |

## ffprobe (verbatim)
```
$ ffprobe ... ep/mp3/neon-voltage.mp3
137.232,5490369
$ ffprobe ... ep/mp3/circuit-breaker.mp3
134.544,5382852
$ ffprobe ... ep/mp3/midnight-protocol.mp3
136.176,5448134
$ ffprobe ... ep/mp3/chrome-hearts.mp3
133.968,5359810
$ ffprobe ... ep/mp3/voltage-drop.mp3
135.072,5403969
$ ffprobe ... ep/mp3/static-bloom.mp3
133.416,5337729
$ ffprobe ... ep/mp3/pulse-reactor.mp3
134.928,5398210
$ ffprobe ... ep/mp3/afterglow-drive.mp3
132.216,5289732
$ ffprobe ... ep/mp3/overdrive.mp3
134.64,5386686
$ ffprobe ... ep/mp3/aurora-circuit.mp3
135.48,5420291
```

## Gate
- duration >= 120s
- |LUFS +14| <= 1
- true peak <= -1.0 dBTP

## Editable modules
```
ep/xm/neon-voltage.xm  14270 bytes
ep/xm/circuit-breaker.xm  12764 bytes
ep/xm/midnight-protocol.xm  11688 bytes
ep/xm/chrome-hearts.xm  14279 bytes
ep/xm/voltage-drop.xm  11099 bytes
ep/xm/static-bloom.xm  12244 bytes
ep/xm/pulse-reactor.xm  14847 bytes
ep/xm/afterglow-drive.xm  11742 bytes
ep/xm/overdrive.xm  13732 bytes
ep/xm/aurora-circuit.xm  13239 bytes
```
