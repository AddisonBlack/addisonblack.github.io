#!/usr/bin/env python3
"""
Generate the synthetic HVAC company dataset behind the portfolio's Power BI projects.

Every company, person and number is made up. The output is deterministic (fixed seed),
so rerunning this script recreates identical files:

    python3 data/generate_data.py

Only the Python standard library is used.
"""
import csv
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SEED = 20261117
rng = random.Random(SEED)

OUT = Path(__file__).resolve().parent
ST_DIR = OUT / "servicetitan"
QB_DIR = OUT / "quickbooks"

SIM_START = date(2023, 1, 1)       # history is simulated from here so a customer base exists on day one
DATA_START = date(2025, 1, 1)      # first date in the exported files
DATA_END = date(2026, 11, 16)      # last date in the exported files (a Monday)
PROGRAM_LAUNCH = date(2025, 6, 1)  # membership follow-up program: later cohorts retain better
FIRST_PAY_PERIOD = date(2024, 12, 29)  # a Sunday; pay periods are biweekly Sunday to Saturday
DOMAIN = "contoso.com"
BASE_NEW_CUSTOMERS = 2200         # new customers in an average month of 2023 (tuned for ~210 technicians)

S_O, D_O, E_O, L_O = (d.toordinal() for d in (SIM_START, DATA_START, DATA_END, PROGRAM_LAUNCH))
MONTH = 30.44


def iso(o):
    return date.fromordinal(o).isoformat() if o else ""


def lognorm(median, sigma):
    return median * math.exp(rng.gauss(0, sigma))


def pick(pairs):
    vals, wts = zip(*pairs)
    return rng.choices(vals, wts)[0]


def write(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


# --------------------------------------------------------------------------- reference data

MALE = """James Michael Robert John David William Richard Joseph Thomas Christopher Charles Daniel
Matthew Anthony Mark Donald Steven Andrew Paul Joshua Kenneth Kevin Brian Timothy Ronald George
Jason Edward Jeffrey Ryan Jacob Nicholas Gary Eric Jonathan Stephen Larry Justin Scott Brandon
Benjamin Samuel Gregory Alexander Patrick Frank Raymond Jack Dennis Jerry Tyler Aaron Jose Adam
Nathan Henry Zachary Douglas Peter Kyle Noah Ethan Jeremy Christian Walter Keith Austin Sean Carl
Dylan Jordan Jesse Bryan Lawrence Arthur Gabriel Bruce Logan Alan Juan Elijah Wayne Randy Mason
Vincent Liam Caleb Bradley Russell Lucas Marcus Derek Travis Cody Shane Luis Carlos Hector Andre
Darnell Malik Trevor Colton Wyatt Hunter Garrett""".split()
FEMALE = """Mary Patricia Jennifer Linda Elizabeth Barbara Susan Jessica Sarah Karen Lisa Nancy
Sandra Margaret Ashley Kimberly Emily Donna Michelle Carol Amanda Melissa Stephanie Rebecca Laura
Cynthia Amy Kathleen Angela Emma Brenda Nicole Anna Samantha Katherine Christine Rachel Maria
Olivia Heather Catherine Diane Julie Victoria Lauren Kelly Christina Andrea Megan Jacqueline
Madison Teresa Abigail Sophia Grace Natalie Danielle Brittany Kayla Alexis""".split()
LAST = """Smith Johnson Williams Brown Jones Garcia Miller Davis Rodriguez Martinez Hernandez Lopez
Gonzalez Wilson Anderson Thomas Taylor Moore Jackson Martin Lee Perez Thompson White Harris Sanchez
Clark Ramirez Lewis Robinson Walker Young Allen King Wright Scott Torres Nguyen Hill Flores Green
Adams Nelson Baker Hall Rivera Campbell Mitchell Carter Roberts Gomez Phillips Evans Turner Diaz
Parker Cruz Edwards Collins Reyes Stewart Morris Morales Murphy Cook Rogers Gutierrez Ortiz Morgan
Cooper Peterson Bailey Reed Kelly Howard Ramos Kim Cox Ward Richardson Watson Brooks Chavez Wood
James Bennett Gray Mendoza Ruiz Hughes Price Alvarez Castillo Sanders Patel Myers Long Ross Foster
Jimenez Powell Jenkins Perry Russell Sullivan Bell Coleman Butler Henderson Barnes Gonzales Fisher
Vasquez Simmons Romero Jordan Patterson Alexander Hamilton Graham Reynolds Griffin Wallace Moreno
West Cole Hayes Bryant Herrera Gibson Ellis Tran Medina Aguilar Stevens Murray Ford Castro Marshall
Owens Harrison Fernandez McDonald Woods Washington Kennedy Wells Vargas Henry Chen Freeman Webb
Tucker Guzman Burns Crawford Olson Simpson Porter Hunter Gordon Mendez Silva Shaw Snyder Mason
Dixon Munoz Hunt Hicks Holmes Palmer Wagner Black Robertson Boyd Rose Stone Salazar Fox Warren
Mills Meyer Rice Schmidt Garza Daniels Ferguson Nichols Stephens Soto Weaver Ryan Gardner Payne
Grant Dunn Kelley Spencer Hawkins Arnold Pierce Hansen Peters Santos Hart Bradley Knight Elliott
Cunningham Duncan Armstrong Hudson Carroll Lane Riley Andrews Ray Berry Perkins Hoffman Johnston
Matthews Pena Richards Willis Carpenter Lawrence Sandoval""".split()
NICKNAMES = {
    "Michael": "Mike", "Robert": "Rob", "William": "Will", "Christopher": "Chris", "Jonathan": "Jon",
    "Matthew": "Matt", "Daniel": "Dan", "Joseph": "Joe", "Anthony": "Tony", "Nicholas": "Nick",
    "Benjamin": "Ben", "Samuel": "Sam", "Alexander": "Alex", "Zachary": "Zach", "Joshua": "Josh",
    "Thomas": "Tom", "James": "Jim", "Timothy": "Tim", "Steven": "Steve", "Patrick": "Pat",
    "Gregory": "Greg", "Jeffrey": "Jeff", "Kenneth": "Ken", "Katherine": "Kate", "Jennifer": "Jen",
}
BUSINESS_SUFFIX = ["Property Management", "Dental Group", "Family Restaurant", "Auto Repair",
                   "Law Office", "Veterinary Clinic", "Community Church", "Fitness Center",
                   "Apartments", "Insurance Agency", "Pediatrics", "Hardware", "Bakery",
                   "Accounting", "Montessori School", "Physical Therapy", "Brewing Co."]
CITIES = [  # (city, ZIP codes, weight)
    ("Columbus", ["43201", "43202", "43204", "43206", "43209", "43211", "43214", "43219", "43220",
                  "43224", "43229", "43231", "43232", "43235"], 30),
    ("Dublin", ["43016", "43017"], 7), ("Westerville", ["43081", "43082"], 8),
    ("Hilliard", ["43026"], 7), ("Grove City", ["43123"], 7), ("Gahanna", ["43230"], 5),
    ("Reynoldsburg", ["43068"], 5), ("Upper Arlington", ["43221"], 5),
    ("Worthington", ["43085"], 4), ("Delaware", ["43015"], 5), ("Powell", ["43065"], 4),
    ("Pickerington", ["43147"], 5), ("New Albany", ["43054"], 3), ("Lewis Center", ["43035"], 4),
    ("Canal Winchester", ["43110"], 3), ("Grandview Heights", ["43212"], 2),
]
LEAD_SOURCES = [("Google Ads", 28), ("Website", 20), ("Referral", 15), ("Phone Book / Other", 8),
                ("Yelp", 8), ("Direct Mail", 9), ("Home Show", 4), ("Facebook", 8)]

# id: (name, trade, type)
BUSINESS_UNITS = {
    1001: ("HVAC Service", "HVAC", "Service"),
    1002: ("HVAC Maintenance", "HVAC", "Maintenance"),
    1003: ("HVAC Install", "HVAC", "Install"),
    1004: ("Plumbing Service", "Plumbing", "Service"),
    1005: ("Plumbing Install", "Plumbing", "Install"),
    1006: ("Electrical", "Electrical", "Service and Install"),
}
SERVICE_BUS = {1001, 1004, 1006}
# id: (name, business unit, class, min hrs, max hrs, median revenue, revenue spread)
JOB_TYPES = {
    201: ("No Cool Diagnostic", 1001, "Repair", 1.0, 2.5, 420, 0.6),
    202: ("No Heat Diagnostic", 1001, "Repair", 1.0, 2.5, 380, 0.6),
    203: ("AC Repair", 1001, "Repair", 1.5, 3.5, 650, 0.5),
    204: ("Furnace Repair", 1001, "Repair", 1.5, 3.5, 560, 0.5),
    205: ("Heat Pump Repair", 1001, "Repair", 1.5, 3.5, 720, 0.5),
    206: ("Thermostat Install", 1001, "Repair", 0.75, 1.5, 340, 0.3),
    211: ("Spring AC Tune-Up", 1002, "Maintenance", 0.75, 1.5, 139, 0.0),
    212: ("Fall Furnace Tune-Up", 1002, "Maintenance", 0.75, 1.5, 139, 0.0),
    221: ("AC Replacement", 1003, "Install", 6, 10, 8900, 0.25),
    222: ("Furnace Replacement", 1003, "Install", 5, 9, 7400, 0.25),
    223: ("Heat Pump System Install", 1003, "Install", 7, 10, 14500, 0.22),
    224: ("Ductless Mini-Split Install", 1003, "Install", 5, 9, 6200, 0.3),
    231: ("Drain Cleaning", 1004, "Repair", 0.75, 2, 290, 0.4),
    232: ("Leak Repair", 1004, "Repair", 1, 3, 480, 0.5),
    233: ("Water Heater Repair", 1004, "Repair", 1, 2.5, 390, 0.4),
    234: ("Fixture Repair", 1004, "Repair", 0.75, 2, 260, 0.4),
    241: ("Water Heater Replacement", 1005, "Install", 3, 6, 2400, 0.2),
    242: ("Tankless Water Heater Install", 1005, "Install", 5, 9, 4600, 0.2),
    243: ("Whole-Home Repipe", 1005, "Install", 8, 10, 9800, 0.3),
    251: ("Outlet and Circuit Repair", 1006, "Repair", 0.75, 2.5, 310, 0.45),
    252: ("Panel Upgrade", 1006, "Install", 5, 8, 3200, 0.25),
    253: ("EV Charger Install", 1006, "Install", 3, 5, 1700, 0.25),
    254: ("Generator Install", 1006, "Install", 8, 10, 11500, 0.25),
}
# which service jobs turn into replacement estimates: job type -> (probability, install types)
ESTIMATE_FROM = {
    201: (0.20, [(221, 5), (223, 3), (224, 2)]),
    202: (0.20, [(222, 6), (223, 3)]),
    203: (0.08, [(221, 6), (223, 3), (224, 1)]),
    204: (0.08, [(222, 7), (223, 3)]),
    205: (0.10, [(223, 1)]),
    233: (0.25, [(241, 7), (242, 3)]),
    232: (0.05, [(243, 1)]),
    251: (0.15, [(252, 5), (253, 3), (254, 2)]),
}
LEAD_INSTALLS = {
    "HVAC": [(221, 4), (222, 3), (223, 3), (224, 2)],
    "Plumbing": [(241, 5), (242, 3), (243, 2)],
    "Electrical": [(252, 4), (253, 4), (254, 2)],
}
TRADE_SALES_BU = {"HVAC": 1003, "Plumbing": 1005, "Electrical": 1006}
NEW_CUSTOMER_SEASON = [1.10, 0.95, 0.85, 0.85, 0.95, 1.20, 1.35, 1.30, 0.95, 0.85, 0.90, 1.10]
REPAIR_SEASON = {
    1001: [1.25, 1.10, 0.80, 0.70, 0.85, 1.30, 1.50, 1.40, 0.90, 0.75, 0.85, 1.15],
    1004: [1.20, 1.15, 1.00, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.00, 1.00, 1.10],
    1006: [1.00, 1.00, 1.00, 1.00, 1.05, 1.10, 1.15, 1.10, 1.00, 0.95, 0.95, 1.00],
}
REPAIR_SPLIT = [(1001, 58), (1004, 30), (1006, 12)]
COOLING_SHARE = [0.10, 0.10, 0.25, 0.40, 0.65, 0.85, 0.90, 0.88, 0.60, 0.30, 0.15, 0.10]
PEAK = 1.5

# billable hours a technician can take in one day, and the average load used to size each team
DAILY_CAP = {1001: 7.0, 1002: 7.5, 1003: 10.0, 1004: 7.0, 1005: 10.0, 1006: 8.0}
PLANNED_LOAD = {1001: 5.0, 1002: 5.2, 1003: 6.6, 1004: 5.0, 1005: 6.2, 1006: 5.2}
LEVELS = ["Apprentice", "Technician I", "Technician II", "Senior Technician", "Lead Technician"]
BASE_RATE = {"Apprentice": 21.0, "Technician I": 26.0, "Technician II": 31.0,
             "Senior Technician": 37.0, "Lead Technician": 43.0}
COMMISSION = {"Apprentice": 0.0, "Technician I": 0.02, "Technician II": 0.03,
              "Senior Technician": 0.04, "Lead Technician": 0.05}


# --------------------------------------------------------------------------- people

used_names = set()


def new_person_name(female_share=0.08):
    while True:
        first = rng.choice(FEMALE if rng.random() < female_share else MALE)
        last = rng.choice(LAST)
        if (first, last) not in used_names:
            used_names.add((first, last))
            return first, last


class Person:
    __slots__ = ("pid", "first", "last", "display_first", "bu", "hire", "term", "prior_years",
                 "prod", "close", "ticket", "lead_weight", "manager", "level", "rate",
                 "commission", "qb_id", "idx")

    def name(self):
        return f"{self.display_first} {self.last}"

    def email(self):
        return f"{self.display_first.lower()}.{self.last.lower()}@{DOMAIN}"

    def active(self, o):
        return self.hire <= o and (self.term is None or o < self.term)


def build_roster(target_fn, initial_hire_range, make):
    """Hire to a monthly headcount target, with random quits. target_fn(ordinal) -> headcount."""
    people, active = [], []
    for _ in range(target_fn(S_O)):
        p = make()
        p.hire = rng.randint(*initial_hire_range)
        people.append(p)
        active.append(p)
    y, m = SIM_START.year, SIM_START.month
    while date(y, m, 1) <= DATA_END:
        mo = date(y, m, 1).toordinal()
        for p in list(active):
            if rng.random() < 0.0095 and mo + 27 > p.hire + 60:
                p.term = mo + rng.randint(0, 27)
                active.remove(p)
        while len(active) < target_fn(mo):
            p = make(new_hire=True)
            p.hire = mo + rng.randint(0, 27)
            people.append(p)
            active.append(p)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    for p in people:
        if p.term is not None and p.term > E_O:
            p.term = None
    return [p for p in people if p.hire <= E_O]


# salespeople
SALES_TARGET = {"HVAC": {2023: 14, 2024: 15, 2025: 16, 2026: 16},
                "Plumbing": {2023: 5, 2024: 5, 2025: 6, 2026: 6},
                "Electrical": {2023: 3, 2024: 4, 2025: 4, 2026: 4}}
salespeople = {}
for trade, targets in SALES_TARGET.items():
    def make_sp(new_hire=False, trade=trade):
        p = Person()
        p.first, p.last = new_person_name(0.25)
        p.display_first = p.first
        p.bu = TRADE_SALES_BU[trade]
        p.term = None
        p.close = rng.uniform(0.28, 0.40) if new_hire else rng.uniform(0.32, 0.60)
        p.ticket = rng.uniform(0.88, 1.18)
        p.lead_weight = rng.uniform(0.7, 1.3)
        return p
    salespeople[trade] = build_roster(
        lambda o, t=targets: t[date.fromordinal(o).year],
        (date(2014, 1, 1).toordinal(), date(2022, 11, 30).toordinal()), make_sp)


def pick_salesperson(trade, o):
    pool = [p for p in salespeople[trade] if p.active(o)]
    return rng.choices(pool, [p.lead_weight for p in pool])[0]


# --------------------------------------------------------------------------- customers and demand

class Job:
    __slots__ = ("jid", "cust", "bu", "jt", "req", "created", "done", "tech", "hours", "amount",
                 "status", "member")


class Estimate:
    __slots__ = ("eid", "cust", "bu", "jt", "sp", "origin", "created", "sold", "status", "total",
                 "install")


class Customer:
    __slots__ = ("cid", "name", "ctype", "city", "zip", "source", "created")


customers, jobs, estimates, memberships = [], [], [], []


def poisson_times(start, end, rate_per_month, season):
    """Event days in (start, end], thinned by a monthly seasonal curve."""
    out, t = [], float(start)
    if rate_per_month <= 0:
        return out
    while True:
        t += rng.expovariate(rate_per_month * PEAK / MONTH)
        if t > end:
            return out
        o = int(t)
        if season is None or rng.random() < season[date.fromordinal(o).month - 1] / PEAK:
            out.append(o)


def add_job(cust, bu, jt, req, created, member, amount=None, cancel_rate=0.04):
    j = Job()
    j.cust, j.bu, j.jt, j.req, j.created, j.member = cust, bu, jt, req, created, member
    j.status = "Canceled" if rng.random() < cancel_rate else "Completed"
    name, _, cls, lo, hi, med, sig = JOB_TYPES[jt]
    commercial = cust.ctype == "Commercial"
    j.hours = round(rng.uniform(lo, hi) * (1.8 if commercial and cls == "Maintenance" else 1) * 4) / 4
    if amount is not None:
        j.amount = amount
    elif cls == "Maintenance":
        j.amount = 0.0 if member else (349.0 if commercial else 139.0)
    else:
        j.amount = round(lognorm(med, sig) * (1.6 if commercial else 1) * (0.85 if member else 1), 2)
    j.done = j.tech = None
    jobs.append(j)
    if j.status == "Completed" and jt in ESTIMATE_FROM and rng.random() < ESTIMATE_FROM[jt][0]:
        make_estimate(cust, j, req + rng.randint(0, 3), ESTIMATE_FROM[jt][1])
    return j


def make_estimate(cust, origin, created, choices):
    if created > E_O:
        return
    jt = pick(choices)
    bu = JOB_TYPES[jt][1]
    trade = BUSINESS_UNITS[bu][1]
    e = Estimate()
    e.cust, e.bu, e.jt, e.origin, e.created = cust, bu, jt, origin, created
    e.sp = pick_salesperson(trade, created)
    med, sig = JOB_TYPES[jt][5], JOB_TYPES[jt][6]
    e.total = float(round(lognorm(med, sig) * e.sp.ticket * (1.35 if cust.ctype == "Commercial" else 1)))
    e.sold, e.install = None, None
    close = e.sp.close * (0.8 if origin is None else 1.0)
    if rng.random() < close:
        sold = created + rng.randint(0, 14)
        if sold <= E_O:
            e.status, e.sold = "Sold", sold
            install_day = sold + rng.randint(5, 25)
            if install_day <= E_O:
                e.install = add_job(cust, bu, jt, install_day, sold, False, e.total, cancel_rate=0.015)
        else:
            e.status = "Open"
    else:
        e.status = "Dismissed" if created + 21 <= E_O else "Open"
    estimates.append(e)


def repair_job(cust, o, member):
    bu = pick(REPAIR_SPLIT)
    m = date.fromordinal(o).month - 1
    if bu == 1001:
        cooling = rng.random() < COOLING_SHARE[m]
        jt = pick([(201 if cooling else 202, 35), (203 if cooling else 204, 35), (205, 20), (206, 10)])
    elif bu == 1004:
        jt = pick([(231, 35), (232, 25), (233, 35 if m in (0, 1, 11) else 25), (234, 15)])
    else:
        jt = 251
    add_job(cust, bu, jt, o, o - rng.choice([0, 0, 0, 1, 1, 2, 3]), member)


def maint_job(cust, o, member):
    jt = 211 if 2 <= date.fromordinal(o).month <= 7 else 212
    lead = rng.randint(10, 30) if member else rng.randint(1, 10)
    add_job(cust, 1002, jt, o, o - lead, member)


def blended_repairs(start, end, rate):
    """Repair calls whose business-unit mix and seasonality vary by month."""
    out = []
    t = float(start)
    if rate <= 0:
        return out
    while True:
        t += rng.expovariate(rate * PEAK / MONTH)
        if t > end:
            return out
        o = int(t)
        m = date.fromordinal(o).month - 1
        blended = sum(REPAIR_SEASON[bu][m] * w for bu, w in REPAIR_SPLIT) / 100
        if rng.random() < blended / PEAK:
            out.append(o)


def simulate_customer(c):
    created = c.created
    commercial = c.ctype == "Commercial"
    r = rng.random()
    first = "lead" if r < 0.08 else ("maint" if r < 0.18 else "repair")
    emergency = first == "repair" and date.fromordinal(created).month in (6, 7, 8)
    launched = created >= L_O

    p_join = 0.13 + (0.12 if launched else 0) + (0.05 if c.source == "Referral" else 0) \
        + (0.08 if commercial else 0) + (0.10 if first == "maint" else 0)
    if first == "lead":
        p_join = 0.0
    member_until = None
    if rng.random() < p_join:
        end, renewals = created + 365, 0
        while end <= E_O:
            renew_p = (0.88 if commercial else 0.80) + (0.06 if end >= L_O else 0)
            if rng.random() >= renew_p:
                break
            end += 365
            renewals += 1
        member_until = end
        memberships.append((c, created, end, renewals))

    # first contact
    if first == "lead":
        trade = pick([("HVAC", 70), ("Plumbing", 15), ("Electrical", 15)])
        make_estimate(c, None, created, LEAD_INSTALLS[trade])
    elif first == "maint":
        add_job(c, 1002, 211 if 2 <= date.fromordinal(created).month <= 7 else 212,
                created, created - rng.randint(1, 7), member_until is not None)
    else:
        repair_job(c, created, member_until is not None)

    lam = 0.14 if commercial else 0.075
    h = 0.040 * (1.6 if emergency else 1) * (0.6 if c.source == "Referral" else 1) \
        * (1.15 if c.source in ("Google Ads", "Yelp") else 1) * (0.75 if launched else 1)

    if member_until is not None:
        stop = min(member_until, E_O)
        for o in blended_repairs(created, stop, lam * 1.15):
            repair_job(c, o, True)
        for y in range(date.fromordinal(created).year, DATA_END.year + 1):
            for v in (rng.randint(date(y, 3, 1).toordinal(), date(y, 6, 10).toordinal()),
                      rng.randint(date(y, 9, 5).toordinal(), date(y, 12, 5).toordinal())):
                if created + 20 < v < member_until and v <= E_O:
                    maint_job(c, v, True)
        nonmember_from = member_until if member_until <= E_O else None
    else:
        nonmember_from = created
    if nonmember_from is not None:
        alive_until = min(E_O, int(nonmember_from + rng.expovariate(h) * MONTH))
        for o in blended_repairs(nonmember_from, alive_until, lam):
            repair_job(c, o, False)
        for o in poisson_times(nonmember_from, alive_until, 0.015, None):
            maint_job(c, o, False)


cid = 104000
y, m = SIM_START.year, SIM_START.month
while date(y, m, 1) <= DATA_END:
    first_o = date(y, m, 1).toordinal()
    last_o = min((date(y + (m == 12), m % 12 + 1, 1)).toordinal() - 1, E_O)
    growth = 1.07 ** ((first_o - S_O) / 365.25)
    n = round(BASE_NEW_CUSTOMERS * NEW_CUSTOMER_SEASON[m - 1] * growth * rng.uniform(0.94, 1.06))
    n = round(n * (last_o - first_o + 1) / (date(y + (m == 12), m % 12 + 1, 1).toordinal() - first_o))
    for _ in range(n):
        c = Customer()
        cid += rng.randint(1, 4)
        c.cid = cid
        c.ctype = "Commercial" if rng.random() < 0.11 else "Residential"
        last = rng.choice(LAST)
        if c.ctype == "Commercial":
            c.name = f"{last} {rng.choice(BUSINESS_SUFFIX)}"
        else:
            c.name = f"{rng.choice(MALE + FEMALE)} {last}"
        city, zips, _ = rng.choices(CITIES, [w for *_, w in CITIES])[0]
        c.city, c.zip = city, rng.choice(zips)
        c.source = pick(LEAD_SOURCES)
        c.created = rng.randint(first_o, last_o)
        customers.append(c)
        simulate_customer(c)
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)

window_jobs = [j for j in jobs if D_O <= j.req <= E_O]

# --------------------------------------------------------------------------- technicians

annual_hours = defaultdict(float)
for j in window_jobs:
    if j.status == "Completed":
        annual_hours[(j.bu, date.fromordinal(j.req).year)] += j.hours
days_2026 = E_O - date(2026, 1, 1).toordinal() + 1
tech_target = {}
for (bu, yr), hrs in annual_hours.items():
    if yr == 2026:
        hrs *= 365 / days_2026
    if bu == 1002:  # tune-ups happen in two seasons, so staff for the busy months
        hrs *= 1.3
    workdays = 250 * 0.955
    tech_target[(bu, yr)] = max(3, round(hrs / (workdays * PLANNED_LOAD[bu])))
for bu in BUSINESS_UNITS:  # staff 2023-2024 at the 2025 level, less growth
    tech_target[(bu, 2024)] = round(tech_target[(bu, 2025)] / 1.07)
    tech_target[(bu, 2023)] = round(tech_target[(bu, 2024)] / 1.07)

technicians, managers = [], {}
for bu in BUSINESS_UNITS:
    n_mgr = max(1, round(tech_target[(bu, 2026)] / 16))
    managers[bu] = []
    for _ in range(n_mgr):
        f, l = new_person_name(0.15)
        managers[bu].append((f"{f} {l}", f"{f.lower()}.{l.lower()}@{DOMAIN}"))

    def make_tech(new_hire=False, bu=bu):
        p = Person()
        p.first, p.last = new_person_name(0.06)
        p.display_first = NICKNAMES[p.first] if p.first in NICKNAMES and rng.random() < 0.45 else p.first
        p.bu, p.term = bu, None
        p.prior_years = rng.choice([0, 0, 0, 1, 2, 3, 5]) if new_hire else rng.choice([0, 0, 1, 2, 4])
        p.prod = rng.uniform(0.75, 1.25)
        p.manager = rng.choice(managers[bu])
        return p
    technicians += build_roster(lambda o, bu=bu: tech_target[(bu, date.fromordinal(o).year)],
                                (date(2009, 1, 1).toordinal(), date(2022, 12, 15).toordinal()),
                                make_tech)
technicians = [t for t in technicians if t.term is None or t.term > D_O]

for i, t in enumerate(technicians):
    t.idx = i
    years = ((t.term or E_O) - t.hire) / 365.25 + t.prior_years
    t.level = LEVELS[0 if years < 1 else 1 if years < 3 else 2 if years < 6 else 3 if years < 10 else 4]
    bump = 1.0 if t.bu in (1003, 1005) else 2.0 if t.bu == 1006 else 0.0
    t.rate = round((BASE_RATE[t.level] + bump + rng.uniform(-1.5, 1.5)) * 4) / 4
    t.commission = COMMISSION[t.level] if t.bu in SERVICE_BUS else 0.0

tech_ids = rng.sample(range(4_100_000, 4_999_999), len(technicians))
for t, tid in zip(technicians, tech_ids):
    t.pid = tid

# paid time off: about 4.5% of weekdays
pto = set()
for t in technicians:
    for o in range(max(t.hire, D_O), (t.term or E_O + 1)):
        if date.fromordinal(o).weekday() < 5 and rng.random() < 0.045:
            pto.add((t.idx, o))

# --------------------------------------------------------------------------- dispatch

by_bu_day = defaultdict(list)
for j in window_jobs:
    if j.status == "Completed":
        by_bu_day[(j.bu, j.req)].append(j)

day_load = defaultdict(float)  # (tech idx, ordinal) -> billable hours
day_jobs = defaultdict(int)
techs_by_bu = defaultdict(list)
for t in technicians:
    techs_by_bu[t.bu].append(t)

for bu in BUSINESS_UNITS:
    carry = []
    for o in range(D_O, E_O + 1):
        today = carry + by_bu_day.get((bu, o), [])
        carry = []
        wd = date.fromordinal(o).weekday()
        if wd == 6 or (wd == 5 and bu not in SERVICE_BUS):
            carry = today
            continue
        week = date.fromordinal(o).isocalendar()[1]
        if wd == 5:  # Saturday on-call rotation, one fifth of the team
            working = [t for t in techs_by_bu[bu] if t.active(o) and (t.idx + week) % 5 == 0]
            cap_scale = 0.75
        else:
            working = [t for t in techs_by_bu[bu] if t.active(o) and (t.idx, o) not in pto]
            cap_scale = 1.0
        if not working:
            carry = today
            continue
        weights = [t.prod for t in working]
        today.sort(key=lambda j: j.req)
        for j in today:
            best = None
            for t in rng.choices(working, weights, k=min(6, len(working))):
                load = day_load[(t.idx, o)]
                if (load == 0 or load + j.hours <= DAILY_CAP[bu] * cap_scale) and \
                        (best is None or load / t.prod < day_load[(best.idx, o)] / best.prod):
                    best = t
            if best is None:
                for t in working:
                    load = day_load[(t.idx, o)]
                    if load == 0 or load + j.hours <= DAILY_CAP[bu] * cap_scale:
                        best = t
                        break
            if best is None:
                carry.append(j)
                continue
            j.tech, j.done = best, o
            day_load[(best.idx, o)] += j.hours
            day_jobs[(best.idx, o)] += 1
    for j in carry:  # still waiting at the end of the export: scheduled, not yet done
        j.status = "Scheduled"

# --------------------------------------------------------------------------- timesheets

timesheets = []  # (tech, ordinal, clock in minutes, clock out minutes, break, minutes worked)
for t in technicians:
    for o in range(max(t.hire, D_O), (t.term or E_O + 1)):
        wd = date.fromordinal(o).weekday()
        load, n = day_load.get((t.idx, o), 0.0), day_jobs.get((t.idx, o), 0)
        if wd == 6 or (wd == 5 and n == 0) or (wd < 5 and (t.idx, o) in pto):
            continue
        hours = load + 0.35 * n + 0.5 + rng.uniform(-0.25, 0.4)
        if wd < 5 and hours < 8 and rng.random() < 0.85:
            hours = 8.0 + rng.uniform(0, 0.2)
        hours = min(hours, 13.0)
        start = (7 * 60 + rng.randint(-10, 40)) if wd < 5 else (8 * 60 + rng.randint(0, 60))
        brk = 30 if hours > 6 else 0
        worked = int(round(hours * 60))
        timesheets.append((t, o, start, start + worked + brk, brk, worked))

# --------------------------------------------------------------------------- IDs

window_jobs.sort(key=lambda j: (j.req, j.bu))
jid = 31_200_000
for j in window_jobs:
    jid += rng.randint(1, 3)
    j.jid = jid
out_estimates = sorted((e for e in estimates if D_O <= e.created <= E_O), key=lambda e: e.created)
eid = 7_800_000
for e in out_estimates:
    eid += rng.randint(1, 2)
    e.eid = eid
for trade_people in salespeople.values():
    for p in trade_people:
        p.pid = rng.randint(900_000, 999_999)

# --------------------------------------------------------------------------- write ServiceTitan files

def hhmm(mins):
    return f"{mins // 60:02d}:{mins % 60:02d}"


counts = {}
counts["servicetitan/business_units.csv"] = write(
    ST_DIR / "business_units.csv", ["BusinessUnitID", "BusinessUnitName", "Trade", "BusinessUnitType"],
    [(k, *v) for k, v in BUSINESS_UNITS.items()])
counts["servicetitan/job_types.csv"] = write(
    ST_DIR / "job_types.csv", ["JobTypeID", "JobTypeName", "BusinessUnitID", "JobClass"],
    [(k, v[0], v[1], v[2]) for k, v in JOB_TYPES.items()])

used_customers = {j.cust.cid for j in window_jobs} | {e.cust.cid for e in out_estimates}
mem_rows = []
mid = 60_000
for c, start, end, renewals in sorted(memberships, key=lambda x: x[1]):
    mid += 1
    if end < D_O or start > E_O:
        continue
    used_customers.add(c.cid)
    com = c.ctype == "Commercial"
    mem_rows.append((mid, c.cid, "Comfort Club Commercial" if com else "Comfort Club Residential",
                     iso(start), iso(end), 399.00 if com else 189.00,
                     "Active" if end > E_O else "Expired", renewals))
counts["servicetitan/customers.csv"] = write(
    ST_DIR / "customers.csv",
    ["CustomerID", "CustomerName", "CustomerType", "City", "State", "ZipCode", "LeadSource", "CreatedDate"],
    [(c.cid, c.name, c.ctype, c.city, "OH", c.zip, c.source, iso(c.created))
     for c in customers if c.cid in used_customers])
counts["servicetitan/memberships.csv"] = write(
    ST_DIR / "memberships.csv",
    ["MembershipID", "CustomerID", "PlanName", "StartDate", "EndDate", "AnnualPrice", "Status", "Renewals"],
    mem_rows)

counts["servicetitan/technicians.csv"] = write(
    ST_DIR / "technicians.csv",
    ["TechnicianID", "TechnicianName", "Email", "BusinessUnitID", "Position", "HireDate",
     "TerminationDate", "Status", "ManagerName", "ManagerEmail"],
    [(t.pid, t.name(), t.email(), t.bu, t.level, iso(t.hire), iso(t.term),
      "Active" if t.term is None else "Inactive", t.manager[0], t.manager[1])
     for t in sorted(technicians, key=lambda t: t.pid)])

all_sales = [p for ps in salespeople.values() for p in ps if p.term is None or p.term > D_O]
counts["servicetitan/salespeople.csv"] = write(
    ST_DIR / "salespeople.csv",
    ["SalespersonID", "SalespersonName", "Email", "BusinessUnitID", "Title", "HireDate",
     "TerminationDate", "Status"],
    [(p.pid, p.name(), p.email(), p.bu,
      {1003: "Comfort Advisor", 1005: "Plumbing Sales Advisor", 1006: "Electrical Sales Advisor"}[p.bu],
      iso(p.hire), iso(p.term), "Active" if p.term is None else "Inactive")
     for p in sorted(all_sales, key=lambda p: p.pid)])

counts["servicetitan/jobs.csv"] = write(
    ST_DIR / "jobs.csv",
    ["JobID", "CustomerID", "BusinessUnitID", "JobTypeID", "TechnicianID", "CreatedDate",
     "CompletedDate", "JobStatus", "BillableHours"],
    [(j.jid, j.cust.cid, j.bu, j.jt, j.tech.pid if j.tech else "", iso(j.created), iso(j.done),
      j.status, j.hours if j.status == "Completed" else 0)
     for j in window_jobs])

inv_rows = []
inv = 5_400_000
for j in sorted((j for j in window_jobs if j.status == "Completed"), key=lambda j: (j.done, j.jid)):
    inv += 1
    tax = round(j.amount * 0.40 * 0.0725, 2)  # sales tax on the materials share of the ticket
    inv_rows.append((inv, j.jid, j.cust.cid, iso(j.done), j.bu, f"{j.amount:.2f}", f"{tax:.2f}",
                     f"{j.amount + tax:.2f}"))
counts["servicetitan/invoices.csv"] = write(
    ST_DIR / "invoices.csv",
    ["InvoiceID", "JobID", "CustomerID", "InvoiceDate", "BusinessUnitID", "Subtotal", "TaxAmount", "Total"],
    inv_rows)

counts["servicetitan/estimates.csv"] = write(
    ST_DIR / "estimates.csv",
    ["EstimateID", "EstimateName", "CustomerID", "BusinessUnitID", "JobTypeID", "SalespersonID",
     "OriginJobID", "CreatedDate", "SoldDate", "Status", "EstimateTotal", "InstallJobID"],
    [(e.eid, JOB_TYPES[e.jt][0], e.cust.cid, e.bu, e.jt, e.sp.pid,
      e.origin.jid if e.origin is not None and e.origin.req >= D_O else "",
      iso(e.created), iso(e.sold), e.status, f"{e.total:.2f}",
      e.install.jid if e.install is not None else "")
     for e in out_estimates])

counts["servicetitan/timesheets.csv"] = write(
    ST_DIR / "timesheets.csv",
    ["TimesheetID", "TechnicianID", "WorkDate", "ClockIn", "ClockOut", "BreakMinutes", "HoursWorked"],
    [(i + 1, t.pid, iso(o), hhmm(a), hhmm(b), brk, f"{w / 60:.2f}")
     for i, (t, o, a, b, brk, w) in enumerate(sorted(timesheets, key=lambda r: (r[1], r[0].pid)))])

# --------------------------------------------------------------------------- write QuickBooks files

qb_ids = rng.sample(range(1100, 9999), len(technicians))
for t, q in zip(technicians, qb_ids):
    t.qb_id = q
counts["quickbooks/employees.csv"] = write(
    QB_DIR / "employees.csv",
    ["EmployeeID", "EmployeeName", "Department", "PayType", "HourlyRate", "CommissionRate",
     "HireDate", "ReleaseDate", "Status"],
    [(t.qb_id, f"{t.last}, {t.first}", BUSINESS_UNITS[t.bu][1], "Hourly", f"{t.rate:.2f}",
      f"{t.commission:.2f}", iso(t.hire), iso(t.term), "Active" if t.term is None else "Inactive")
     for t in sorted(technicians, key=lambda t: t.qb_id)])

periods = []
p_start = FIRST_PAY_PERIOD.toordinal()
pid = 0
while p_start <= E_O:
    pid += 1
    p_end, pay = p_start + 13, p_start + 19
    status = "Paid" if pay <= E_O else ("Ready to Run" if p_end < E_O else "Open")
    periods.append((pid, p_start, p_end, pay, status))
    p_start += 14
counts["quickbooks/pay_periods.csv"] = write(
    QB_DIR / "pay_periods.csv", ["PayPeriodID", "PeriodStart", "PeriodEnd", "PayDate", "Status"],
    [(a, iso(b), iso(c), iso(d), s) for a, b, c, d, s in periods])

week_minutes = defaultdict(int)  # (tech idx, week start ordinal) -> minutes
for t, o, _, _, _, w in timesheets:
    week_minutes[(t.idx, o - (date.fromordinal(o).weekday() + 1) % 7)] += w
period_sales = defaultdict(float)
for j in window_jobs:
    if j.status == "Completed":
        period_sales[(j.tech.idx, (j.done - FIRST_PAY_PERIOD.toordinal()) // 14 + 1)] += j.amount

register = []
anomalies = 0
for pid, ps, pe, pay, status in periods:
    if status != "Paid":
        continue
    for t in technicians:
        weeks = [week_minutes.get((t.idx, ps), 0) / 60, week_minutes.get((t.idx, ps + 7), 0) / 60]
        if sum(weeks) == 0:
            continue
        reg = sum(min(40.0, w) for w in weeks)
        ot = sum(max(0.0, w - 40) for w in weeks)
        reg, ot = round(reg, 2), round(ot, 2)
        commission = round(period_sales.get((t.idx, pid), 0.0) * t.commission, 2)
        r = rng.random()
        if r < 0.006:      # hours keyed in wrong
            if ot > 0 and rng.random() < 0.5:
                ot = round(max(0.0, ot + rng.choice([-1, 1]) * rng.uniform(1, 6)), 2)
            else:
                reg = round(reg + rng.choice([-1, 1]) * rng.uniform(2, 8), 2)
            anomalies += 1
        elif r < 0.009 and commission > 0:  # commission left off
            commission = 0.0
            anomalies += 1
        reg_pay, ot_pay = round(reg * t.rate, 2), round(ot * t.rate * 1.5, 2)
        register.append((pid, iso(pay), t.qb_id, f"{reg:.2f}", f"{ot:.2f}", f"{t.rate:.2f}",
                         f"{reg_pay:.2f}", f"{ot_pay:.2f}", f"{commission:.2f}",
                         f"{reg_pay + ot_pay + commission:.2f}"))
counts["quickbooks/payroll_register.csv"] = write(
    QB_DIR / "payroll_register.csv",
    ["PayPeriodID", "PayDate", "EmployeeID", "RegularHours", "OvertimeHours", "HourlyRate",
     "RegularPay", "OvertimePay", "Commission", "GrossPay"],
    register)

# --------------------------------------------------------------------------- summary

print("Rows written:")
for k, v in counts.items():
    size = (OUT / k).stat().st_size / 1e6
    print(f"  {k:36s} {v:>9,}  {size:6.1f} MB")
active_end = [t for t in technicians if t.active(E_O)]
print(f"\nTechnicians active on {DATA_END}: {len(active_end)} (all-time in export: {len(technicians)})")
for bu, (name, *_) in BUSINESS_UNITS.items():
    team = [t for t in technicians if t.bu == bu]
    days = sum(1 for (i, o), n in day_jobs.items() if technicians[i].bu == bu)
    n_jobs = sum(n for (i, o), n in day_jobs.items() if technicians[i].bu == bu)
    hrs = sum(h for (i, o), h in day_load.items() if technicians[i].bu == bu)
    print(f"  {name:18s} techs {len(team):3d}  jobs/day {n_jobs / max(days, 1):.2f}  "
          f"billable hrs/day {hrs / max(days, 1):.2f}")
ot_total = sum(float(r[4]) for r in register)
reg_total = sum(float(r[3]) for r in register)
print(f"Overtime share of paid hours: {ot_total / (ot_total + reg_total):.1%}")
print(f"Payroll register rows with a planted error: {anomalies}")
print(f"Scheduled (not yet dispatched) jobs at export: {sum(1 for j in window_jobs if j.status == 'Scheduled')}")
