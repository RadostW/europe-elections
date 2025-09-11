# Data sources

## NUTS 3 codes and names

Names and numeric codes are easiest found on Wikipedia.

[Wikipedia: NUTS regions of Poland.](https://en.wikipedia.org/wiki/NUTS_statistical_regions_of_Poland)

## TERYT codes for powiats

Polish statistical office gives csv files with administrative division information.
[E-teryt](https://eteryt.stat.gov.pl/eTeryt/rejestr_teryt/udostepnianie_danych/baza_teryt/uzytkownicy_indywidualni/wyszukiwanie/wyszukiwanie.aspx?contrast=default)

TERYT codes that can cause problems:
3299, 2299 - ships registered in respective voivodships.
1499 - voters in foreign lands, counted as part of Warsaw.
1431 - old code for Warsaw.
0263 - old code for Wałbrzych.

3218 (łobeski), 2819 (węgorzewski), 2216 (sztumski), 1021 (brzeziński), 2818 (gołdapski), 1821 (leski), 0812 (wschowski) - created in 2002.

## Teritorial and NUTS coding data

Baza Danych Lokalnych (BDL) - *eng. Local Statistics Database* - service ran by Polish Statistical Office offering various socio-economic data (and administrative data).
BDL offers good JSON api which was used.

[BDL api.](https://bdl.stat.gov.pl/api/v1/units?format=json&level=0&page-size=100&page=0)

## Election data

Krajowe Biuro Wyborcze (KBW) - *eng. National Election Office* - government agency responsible for election data

[KBW electoral data sheets.](https://danewyborcze.kbw.gov.pl/indexc4fa.html?title=Strona_g%C5%82%C3%B3wna)

## Shapefiles

Shapefiles for nuts regions can be downloaded from eurostat. These were modified outside of this repository. 
[Eurostat shapefiles](https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics)
