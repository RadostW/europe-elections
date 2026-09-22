import unidecode
import re


def normalize(x):
    l1 = re.sub("[^0-9a-z ]", " ", unidecode.unidecode(x).lower())
    return l1


encountered_names = [
    "2RK Párt",
    "A HAZA NEM ELADÓ",
    "A HAZA NEM ELADÓ MOZGALOM PÁRT",
    "BOLGÁR ORSZÁGOS ÖNKORMÁNYZAT",
    "CENTRUM",
    "CENTRUM ÖSSZEFOGÁS MAGYARORSZÁGÉRT",
    "CENTRUM Összefogás Magyarországért",
    "CIVIL MOZGALOM",
    "CIVILEK",
    "CSALÁDOK PÁRTJA",
    "Civil Mozgalom",
    "DEMOKRATIKUS KOALÍCIÓ",
    "DEMOKRATIKUS KOALÍCIÓ-JOBBIK MAGYARORSZÁGÉRT MOZGALOM-MOMENTUM MOZGALOM-MAGYAR SZOCIALISTA PÁRT-LMP - MAGYARORSZÁG ZÖLD PÁRTJA-PÁRBESZÉD MAGYARORSZÁGÉRT PÁRT",
    "DK",
    "DK-MSZP-Párbeszéd- ZÖLDEK",
    "EGYÜTT - A KORSZAKVÁLTÓK PÁRTJA",
    "EGYÜTT 2014",
    "EGYÜTT-PM",
    "EURÓPAI ROMA KERESZTÉNYEK JOBBLÉTÉÉRT DEMOKRATIKUS PÁRT",
    "FIDESZ",
    "FIDESZ - KDNP",
    "FIDESZ - MAGYAR POLGÁRI SZÖVETSÉG KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ - MAGYAR POLGÁRI SZÖVETSÉG-KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ - Magyar Polgári Szövetség Kereszténydemokrata Néppárt",
    "FIDESZ MAGYAR POLGÁRISZÖVETSÉG KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ MDF",
    "FIDESZ Magyar Polgári Szövetség Kersztény Demokrata Néppárt",
    "FIDESZ- MAGYAR POLGÁRI SZÖVETSÉG KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ- Magyar Polgári Szövetség KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ-KDNP",
    "FIDESZ-MAGYAR POLGÁRI SZÖVETSÉG KERESZTÉNYDEMOKRATA  NÉPPÁRT",
    "FIDESZ-MAGYAR POLGÁRI SZÖVETSÉG KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ-MAGYARPOLGÁRI SZÖVETSÉG KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ-MDF",
    "FIDESZ-Magyar Polgári Szövetség KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ-Magyar Polgári Szövetség Kereszténydemokrata Néppárt",
    "FIDESZ-MagyarPolgári Szövetség KERESZTÉNYDEMOKRATA NÉPPÁRT",
    "FIDESZ-MagyarPolgári Szövetség Kereszténydemokrata Néppárt",
    "Fidesz-KDNP",
    "Fidesz-Magyar Polgári Szövetség Kereszténydemokrata Néppárt",
    "FÜGGETLEN KISGAZDA -, NEMZETI EGYSÉG PÁRT",
    "FÜGGETLEN KISGAZDA FÖLDMUNKÁS ÉS POLGÁRI PÁRT",
    "FÜGGETLEN KISGAZDA, FÖLDMUNKÁS ÉS POLGÁRI PÁRT",
    "FÜGGETLEN KISGAZDA-, NEMZETI EGYSÉG PÁRT",
    "FÜGGETLEN KISGAZDAPÁRT",
    "Független Kisgazda-, Nemzeti Egység Párt",
    "IRÁNYTŰ PÁRT",
    "JESZ",
    "JOBBIK",
    "JOBBIK MAGYARORSZÁGÉRT MOZGALOM",
    "Jobbik",
    "KELL AZ ÖSSZEFOGÁS PÁRT",
    "KERESSZTÉNYDEMOKRATAPÁRT- KERESZTÉNYSZOCIÁLIS CENTRUM ÖSSZEFOGÁS",
    "KERESZTÉNYDEMOKRATAPÁRT - KERESZTÉNYSZOCIÁLIS CENTRUM ÖSSZEFOGÁS",
    "KERESZTÉNYDEMOKRATAPÁRT KERESZTÉNYSZOCIÁLIS CENTRUM ÖSSZEFOGÁS",
    "KERESZTÉNYDEMOKRATAPÁRT- KERESZTÉNYSZOCIÁLIS CENTRUM ÖSSZEFOGÁS",
    "KISGAZDAPÁRT",
    "KTI",
    "Kereszténydemokratapárt Keresztényszociális Centrum Összefogás",
    "KÖZÖS NEVEZŐ 2018",
    "LEHET MÁS A POLITIKA",
    "LMP",
    "LMP – Zöldek",
    "LMP-HP",
    "Lehet Más a Politika",
    "MAGYAR  SZOCIALISTA PÁRT",
    "MAGYAR DEMOKRATA FORUM",
    "MAGYAR DEMOKRATA FÓRUM",
    "MAGYAR IGAZSÁG ÉS ÉLET PÁRJA",
    "MAGYAR IGAZSÁG ÉS ÉLET PÁRTJA",
    "MAGYAR KOMMUNISTA MUNKÁSPÁRT",
    "MAGYAR KÉTFARKÚ KUTYA PÁRT",
    "MAGYAR MUNKÁSPÁRT",
    "MAGYAR SZOCIALISTA PÁRT",
    "MAGYAR SZOCIALISTA PÁRT-PÁRBESZÉD MAGYARORSZÁGÉRT PÁRT",
    "MAGYAR VIDÉK ÉS POLGÁRI PÁRT",
    "MAGYAROK EGYMÁSÉRT SZÖVETSÉGE",
    "MAGYARORSZÁGI CIGÁNYPÁRT",
    "MAGYARORSZÁGI GÖRÖGÖK ORSZÁGOS ÖNKORMÁNYZATA",
    "MAGYARORSZÁGI MUNKÁSPÁRT 2006",
    "MAGYARORSZÁGI NÉMETEK ORSZÁGOS ÖNKORMÁNYZATA",
    "MAGYARORSZÁGI ROMÁNOK ORSZÁGOS ÖNKORMÁNYZATA",
    "MAGYARORSZÁGON ÉLŐ DOLGOZÓ ÉS TANULÓ EMBEREK PÁRTJA",
    "MAVEP",
    "MCF ROMA Ö.",
    "MCF ROMA ÖSSZEFOGÁS PÁRT",
    "MCF Roma Összefogás Párt",
    "MCP",
    "MDF",
    "MEGOLDÁS MOZGALOM",
    "MEMO",
    "MI HAZÁNK",
    "MI HAZÁNK MOZGALOM",
    "MIÉP",
    "MIÉP - JOBBIK A HARMADIK ÚT",
    "MIÉP- Jobbik a Harmadik Út",
    "MIÉP-JOBBIK A HARMADIK ÚT",
    "MIÉP-Jobbik a Harmadik Út",
    "MKKP",
    "MMN",
    "MOMENTUM",
    "MOMENTUM MOZGALOM",
    "MRP",
    "MSZDP",
    "MSZP",
    "MSZP-EGYÜTT-DK-PM-MLP",
    "MSZP-PÁRBESZÉD",
    "MUNKÁSPÁRT",
    "Magyar Demokrata Fórum",
    "Magyar Kommunista Munkáspárt",
    "Magyar Szocialista Párt",
    "Mi Hazánk",
    "Momentum",
    "Munkáspárt",
    "NET PÁRT",
    "NORMÁLIS ÉLET PÁRTJA",
    "ORSZÁGOS HORVÁT ÖNKORMÁNYZAT",
    "ORSZÁGOS LENGYEL ÖNKORMÁNYZAT",
    "ORSZÁGOS RUSZIN ÖNKORMÁNYZAT",
    "ORSZÁGOS SZLOVÁK ÖNKORMÁNYZAT",
    "ORSZÁGOS SZLOVÉN ÖNKORMÁNYZAT",
    "ORSZÁGOS ÖRMÉNY ÖNKORMÁNYZAT",
    "REFORM KISGAZDAPÁRT",
    "REND ÉS ELSZÁMOLTATÁS PÁRT",
    "RKGP",
    "SEM",
    "SERES MÁRIA SZÖVETSÉGESEI",
    "SMS",
    "SPORTOS ÉS EGÉSZSÉGES MAGYARORSZÁGÉRT PÁRT",
    "SZABAD DEMOKRATÁK SZÖVETSÉGE",
    "SZABAD DEMOKRATÁK SZÖVETSÉGE - A MAGYAR LIBERÁLIS PÁRT",
    "SZABAD DEMOKRATÁK SZÖVETSÉGE A MAGYAR LIBERÁLIS PÁRT",
    "SZABAD DEMOKRATÁK SZÖVETSÉGE- A MAGYAR LIBERÁLIS PÁRT",
    "SZABAD DEMOKRATÁK SZÖVETSÉGE-A MAGYAR LIBERÁLIS PÁRT",
    "SZDSZ",
    "SZEGÉNY EMBEREK MAGYARORSZÁGÉRT PÁRT",
    "SZERB ORSZÁGOS ÖNKORMÁNYZAT",
    "SZOCIÁLDEMOKRATA PÁRT",
    "SZOCIÁLDEMOKRATÁK",
    "Szabad Demokraták Szövetsége",
    "Szabad Demokraták Szövetsége a Magyar Liberális Párt",
    "Szabad Demokraták Szövetsége- a Magyar Liberális Párt",
    "TENNI AKARÁS MOZGALOM",
    "TISZA",
    "UKRÁN ORSZÁGOS ÖNKORMÁNYZAT",
    "ZÖLDEK PÁRTJA",
    "dk",
    "eligible_voters",
    "fidesz",
    "issued_ballots",
    "mi_hazank",
    "mkkp",
    "tisza",
    "ÖSSZEFOGÁS",
    "ÖSSZEFOGÁS PÁRT",
    "Összefogás Párt BAZ M-i Lista",
    "ÚDP",
    "ÚJ BAL",
    "ÚJ BALOLDAL",
    "ÚJ-BAL",
    "ÚMP",
]

name_variants = dict()

for raw_name in encountered_names:

    norm_name = normalize(raw_name)

    if (
        re.sub(r"magyarorszagi (.*) orszagos onkormanyzata", r"\1", norm_name)
        != norm_name
    ):
        norm_name = "m o o " + re.sub(
            r"magyarorszagi (.*) orszagos onkormanyzata", r"\1", norm_name
        )

    if re.sub(r"orszagos (.*) onkormanyzat", r"\1", norm_name) != norm_name:
        norm_name = "o o " + re.sub(r"orszagos (.*) onkormanyzat", r"\1", norm_name)

    if re.sub(r"(.*) orszagos onkormanyzat", r"\1", norm_name) != norm_name:
        norm_name = "o o " + re.sub(r"(.*) orszagos onkormanyzat", r"\1", norm_name)

    if "fuggetlen kisgazda" in norm_name:
        norm_name = "fkgp"

    if "egyutt" in norm_name:
        norm_name = "egyutt"

    if "jobbik" in norm_name and "demokratikus" in norm_name:
        norm_name = "dk-jobbik-momentum-mszp-lmp-parbeszed"
    elif "jobbik" in norm_name and "miep" not in norm_name:
        norm_name = "jobbik"
    elif "miep" in norm_name and "jobbik" in norm_name:
        norm_name = "miep jobbik"

    if "fidesz" in norm_name:
        norm_name = "fidesz"

    if "lehet" in norm_name and "mas" in norm_name:
        norm_name = "lmp"

    if "lmp   zoldek" == norm_name:
        norm_name = "lmp"

    if "munkas" in norm_name:
        norm_name = "munkas"

    if "centrum" in norm_name:
        norm_name = "centrum"

    if "momentum" in norm_name:
        norm_name = "momentum"

    if "civil" in norm_name:
        norm_name = "civilek"

    if "magyar" in norm_name and "szocialista" in norm_name:
        norm_name = "mszp"

    if "magyar igazsag es elet parja" in norm_name:
        norm_name = "miep"

    if "magyar igazsag es elet partja" in norm_name:
        norm_name = "miep"

    if (
        "szabad" in norm_name
        and "demokratak" in norm_name
        and "szovetsege" in norm_name
    ):
        norm_name = "szdsz"

    if "mi" in norm_name and "hazank" in norm_name:
        norm_name = "mi hazank"

    if "demokrata" in norm_name and "forum" in norm_name:
        norm_name = "mdf"

    if "a haza nem" in norm_name:
        norm_name = "a haza nem"

    if "keresztenydemokratapart" in norm_name:
        norm_name = "keresztenydemokratapart"

    if norm_name not in name_variants.keys():
        name_variants[norm_name] = []

    name_variants[norm_name].append(raw_name)

reps = []
for norm_name, variants in name_variants.items():
    for variant in variants:
        reps.append((norm_name,variant))

raise NotImplementedError("Party abbreviations were post processed manually further")        