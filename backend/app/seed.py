from app.repositories.database import get_engine
from app.repositories.seed import seed_complaints


GROUPS = [
    ("water", [
        ("high", "Burst water pipe since fajr; water is entering houses.", "Street 12, G-9 Islamabad"),
        ("normal", "Bhai, no water supply in our gali for two days.", "Gali 4, Rawalpindi"),
        ("high", "Tap water smells like sewage; children are drinking it.", "Block B, Satellite Town"),
        ("normal", "Water tanker did not arrive at the promised time.", "Sector I-10, Islamabad"),
        ("low", "Public park tap keeps dripping throughout the day.", "Jinnah Park, Rawalpindi"),
    ]),
    ("electricity", [
        ("high", "A live electricity wire has fallen near the school gate.", "School Road, Hasilpur"),
        ("normal", "Our transformer has stopped working since last night.", "Block C, Hasilpur"),
        ("high", "Sparks are coming from the electricity pole near shops.", "Main Bazaar, Rawalpindi"),
        ("normal", "Voltage keeps dropping and our fans barely run.", "Street 8, G-11 Islamabad"),
        ("low", "Electricity meter box cover is loose but wires are enclosed.", "Lane 3, Model Town"),
    ]),
    ("sanitation", [
        ("normal", "Kachra has not been collected from our street this week.", "Street 5, Hasilpur"),
        ("high", "Sewage is overflowing outside the primary school.", "School Lane, Rawalpindi"),
        ("normal", "Open drain is blocked with plastic bags and rubbish.", "Gali 7, Satellite Town"),
        ("low", "The public waste bin lid is broken and needs replacement.", "Central Park, Islamabad"),
        ("normal", "Please clean the rubbish dumped beside the vegetable mandi.", "Sabzi Mandi, Hasilpur"),
    ]),
    ("roads", [
        ("high", "A deep road hole caused a motorcycle accident this morning.", "Main Road, Hasilpur"),
        ("normal", "Several potholes are damaging cars near the bus stop.", "Bus Stand Road, Rawalpindi"),
        ("normal", "Road dug for pipe repairs has not been restored.", "Street 10, G-9 Islamabad"),
        ("low", "Pedestrian crossing paint has faded near the market.", "Market Road, Model Town"),
        ("high", "An uncovered manhole is in the middle of the busy road.", "Committee Chowk, Rawalpindi"),
    ]),
    ("streetlights", [
        ("normal", "Three streetlights in our gali have been off for a week.", "Gali 2, Hasilpur"),
        ("high", "Streetlight pole is leaning badly over the footpath.", "Park Road, Islamabad"),
        ("low", "Streetlight stays on during the day; please fix its timer.", "Street 6, Satellite Town"),
        ("normal", "The road to the bus stop becomes completely dark at night.", "Bus Stop Lane, Hasilpur"),
        ("normal", "Streetlight flickers constantly outside the clinic.", "Clinic Road, Rawalpindi"),
    ]),
    ("other", [
        ("normal", "Stray dogs are chasing pedestrians near the market.", "Old Bazaar, Hasilpur"),
        ("low", "The public park bench is broken and needs repair.", "Family Park, Islamabad"),
        ("normal", "A shop has blocked the public footpath with goods.", "Commercial Market, Rawalpindi"),
        ("low", "The street name sign is missing; visitors cannot find us.", "Street 9, Model Town"),
        ("high", "A large damaged tree branch may fall on passing people.", "College Road, Hasilpur"),
    ]),
]

STATUSES = ("open", "in_progress", "resolved", "rejected", "open")


def main() -> None:
    samples = []
    for category, complaints in GROUPS:
        for index, (priority, complaint, location) in enumerate(complaints):
            samples.append({
                "text": complaint,
                "location": location,
                "category": category,
                "priority": priority,
                "status": STATUSES[index],
                "ai_summary": complaint,
            })

    try:
        inserted, total = seed_complaints(samples)
        print(f"Inserted: {inserted}; total complaints: {total}")
    finally:
        get_engine().dispose()


if __name__ == "__main__":
    main()
