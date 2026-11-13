# Bundled fonts

These are unmodified upstream TrueType fonts, distributed under the SIL Open Font License 1.1. Each family retains its original license and copyright notice in this directory. The font licenses apply independently of the application code.

Source Sans Pro: Adobe release `2.045R-ro/1.095R-it` (upright 2.045, italic 1.095), revision `ce77773581f4d454f0fa985c073bb25c721bfcf5`.

IBM Plex Mono: Google Fonts distribution, revision `01d5d9f05246fb7090a8403b81257535cb1a088b`.

STIX Two Math: official [STIX Fonts release `v2.13`](https://github.com/stipub/stixfonts/releases/tag/v2.13), static TrueType math font. Used only for equations, with its original `OFL.txt`. Its OpenType MATH table supports native Chromium equation layout; the TrueType version also permits explicit PDF font identity/embedding checks.

Upstream sources: [Adobe Source Sans](https://github.com/adobe-fonts/source-sans/releases/tag/2.045R-ro%2F1.095R-it) and [Google Fonts IBM Plex Mono](https://github.com/google/fonts/tree/01d5d9f05246fb7090a8403b81257535cb1a088b/ofl/ibmplexmono).

The original Source Sans Pro release is used deliberately to retain its family/PostScript names. The fonts have not been renamed, modified, or converted to Source Sans 3. They are copied into the temporary render directory and loaded through local CSS `@font-face` rules. No system installation or runtime font download is needed.

| File | SHA-256 | Upstream download |
| --- | --- | --- |
| `source-sans-pro/SourceSansPro-Regular.ttf` | `c6f835b6a6d942b196e2607bf73a7b086407ae8dbdc928c23a2fb4893ec383f6` | [source](https://raw.githubusercontent.com/adobe-fonts/source-sans/ce77773581f4d454f0fa985c073bb25c721bfcf5/TTF/SourceSansPro-Regular.ttf) |
| `source-sans-pro/SourceSansPro-Semibold.ttf` | `72bf9aa2e78b8c78444ae74b6be09411d5fb5bf0eb9bcdfd47082cc5d9b536df` | [source](https://raw.githubusercontent.com/adobe-fonts/source-sans/ce77773581f4d454f0fa985c073bb25c721bfcf5/TTF/SourceSansPro-Semibold.ttf) |
| `source-sans-pro/SourceSansPro-Bold.ttf` | `8d869f2aeac0220984a430120af819fbcb12a88e8ea4ad72aae4c5f6d6a2b985` | [source](https://raw.githubusercontent.com/adobe-fonts/source-sans/ce77773581f4d454f0fa985c073bb25c721bfcf5/TTF/SourceSansPro-Bold.ttf) |
| `source-sans-pro/SourceSansPro-It.ttf` | `8fa3fe523cb385c2184e6691821c0431a5189a2a01a708a7b047847e15536b03` | [source](https://raw.githubusercontent.com/adobe-fonts/source-sans/ce77773581f4d454f0fa985c073bb25c721bfcf5/TTF/SourceSansPro-It.ttf) |
| `source-sans-pro/LICENSE.txt` | `e1d1fdcefb57985226c06fa9500d29caacfa2b1f8b8c74db911f13c6cad186a1` | [source](https://raw.githubusercontent.com/adobe-fonts/source-sans/ce77773581f4d454f0fa985c073bb25c721bfcf5/LICENSE.txt) |
| `ibm-plex-mono/IBMPlexMono-Regular.ttf` | `6a3412f058c7d8dfd9170c41e85ade48e5156ecb89356110ca57a0a27734af46` | [source](https://raw.githubusercontent.com/google/fonts/01d5d9f05246fb7090a8403b81257535cb1a088b/ofl/ibmplexmono/IBMPlexMono-Regular.ttf) |
| `ibm-plex-mono/IBMPlexMono-Bold.ttf` | `ac27abd6450a64dd94467580a02fe6235156d5b92f2926ebbc8e7489df64e0be` | [source](https://raw.githubusercontent.com/google/fonts/01d5d9f05246fb7090a8403b81257535cb1a088b/ofl/ibmplexmono/IBMPlexMono-Bold.ttf) |
| `ibm-plex-mono/IBMPlexMono-Italic.ttf` | `3362fc791b0652193328b862c1c5f23a789bc7288b1617fa63302f88689a2a34` | [source](https://raw.githubusercontent.com/google/fonts/01d5d9f05246fb7090a8403b81257535cb1a088b/ofl/ibmplexmono/IBMPlexMono-Italic.ttf) |
| `ibm-plex-mono/OFL.txt` | `7e6b2818edbd8f6a01ae80641cc8f16a51080d08fb4e532be3a0b6f74adb07da` | [source](https://raw.githubusercontent.com/google/fonts/01d5d9f05246fb7090a8403b81257535cb1a088b/ofl/ibmplexmono/OFL.txt) |
| `stix-two-math/STIXTwoMath-Regular.ttf` | `2e0331951fd61efb60e4247db7e1b6b7f516f224987d6290c1d45437809a0977` | [source](https://raw.githubusercontent.com/stipub/stixfonts/v2.13/fonts/static_ttf/STIXTwoMath-Regular.ttf) |
| `stix-two-math/OFL.txt` | `bec17cee6412788db45fd2644b301afbc99cc5d372ddd3345dc4a7bfdefb9f04` | [source](https://raw.githubusercontent.com/stipub/stixfonts/v2.13/OFL.txt) |
