# Election data from European countries

## Abstract

This repository contains raw data about elections (public domain unless specified otherwise), and provides metadata to aggregate into NUTS regions to be used with, for example, Eurostat datasets.

## Countries covered
| Country | Years      | Election Types            | Resolution                      | Data Source | Download | Metadata |
|---------|------------|---------------------------|---------------------------------|-------------|----------|----------|
| Poland  | 2000-2025  | sejm, president, european | powiat (380 units, 75k persons) | [1]         | [CSV](./data/downloads/poland.csv)  | [Metadata](./data/downloads/poland_metadata.csv)  |
| Germany | 1990-2025  | bundestag, european       | kreis (400 units, 200k persons) | [2,3]       | [CSV](./data/downloads/germany.csv) | [Metadata](./data/downloads/germany_metadata.csv) |

You can use metadata files to aggregate election results at the desired level.

references:
 - [1] - Own work based on [Dane Wyborcze KBW](https://danewyborcze.kbw.gov.pl).
 - [2] - Own work based on [Bundeswahlleiterin](https://www.bundeswahlleiterin.de/europawahlen/2024/publikationen.html) european results and [BBSR cross tables](https://www.bbsr.bund.de/BBSR/DE/forschung/raumbeobachtung/Raumabgrenzungen/umstiegsschluessel/umsteigeschluessel.html)
 - [3] - Recoding of [GERDA](https://github.com/awiedem/german_election_data) project.

## How to cite

*Harmonised results of some European elections* Radost Waszkiewicz; (2025)
```bibtex
@other{Waszkiewicz_2025
  title={Harmonised results of some European elections},
  author={Waszkiewicz, Radost},
  year={2025}
}
```

AND

*GERDA: The German Election Database.* V. Heddesheimer, H. Hilbig, F. Sichart, & A. Wiedemann; Sci. Data, 12(1), 618. (2025)

```bibtex
@article{Heddesheimer_2025,
  title={GERDA: The German Election Database},
  author={Heddesheimer, Vincent and Hilbig, Hanno and Sichart, Florian and Wiedemann, Andreas},
  journal={Scientific Data},
  volume={12},
  number={1},
  pages={618},
  year={2025},  
}
```

## License

All software in this repository is licensed under GPL v 3.0 or later.

Copyright (C) 2025 Radost Waszkiewicz
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License 
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. 

Raw datasets are public domain unless stated otherwise. Derived datasets are licensed under CC-BY-SA 4.0, or CC-BY-SA 3.0, or GPL v 3.0 or later, at the users choice.
