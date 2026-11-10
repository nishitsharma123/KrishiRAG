import re
from typing import List, Tuple

# Comprehensive agricultural knowledge dictionary for tagging ICAR chunks
CROP_DICTIONARY = {
    "Wheat": [r"\bwheat\b", r"\bgehun\b", r"\btriticum\b", r"\brabi wheat\b"],
    "Rice / Paddy": [r"\brice\b", r"\bpaddy\b", r"\bdhan\b", r"\boryza\b", r"\bbasmati\b"],
    "Maize": [r"\bmaize\b", r"\bcorn\b", r"\bmakka\b", r"\bzea mays\b"],
    "Mustard / Rapeseed": [r"\bmustard\b", r"\brapeseed\b", r"\bsarson\b", r"\btoria\b", r"\braya\b", r"\bbrassica\b"],
    "Chickpea / Gram": [r"\bchickpea\b", r"\bgram\b", r"\bchana\b", r"\bcicer\b", r"\bbengal gram\b"],
    "Cotton": [r"\bcotton\b", r"\bkapas\b", r"\bgossypium\b", r"\bbt cotton\b"],
    "Sugarcane": [r"\bsugarcane\b", r"\bganna\b", r"\bsaccharum\b"],
    "Pigeonpea / Arhar": [r"\bpigeonpea\b", r"\barhar\b", r"\btur\b", r"\bcajanus\b"],
    "Soybean": [r"\bsoybean\b", r"\bsoya\b", r"\bglycine max\b"],
    "Potato": [r"\bpotato\b", r"\baloo\b", r"\bsolanum tuberosum\b"],
    "Tomato": [r"\btomato\b", r"\btamatar\b", r"\blycopersicon\b"],
    "Millets": [r"\bmillet\b", r"\bbajra\b", r"\bjowar\b", r"\bragi\b", r"\bsorghum\b", r"\bpearl millet\b"],
    "Pulses": [r"\bpulse\b", r"\bdal\b", r"\blentil\b", r"\bmasoor\b", r"\bmoong\b", r"\burd\b", r"\burad\b"],
}

TOPIC_DICTIONARY = {
    "Disease Management": [
        r"\bdisease\b", r"\brust\b", r"\bblight\b", r"\bsmut\b", r"\bmildew\b", r"\brot\b", 
        r"\bwilt\b", r"\bfungus\b", r"\bfungal\b", r"\bpathogen\b", r"\bpropiconazole\b",
        r"\bmancozeb\b", r"\bcarbendazim\b", r"\btebuconazole\b", r"\byellow rust\b", r"\bbrown rust\b"
    ],
    "Pest Management": [
        r"\bpest\b", r"\binsect\b", r"\bborer\b", r"\baphid\b", r"\bbollworm\b", r"\bwhitefly\b",
        r"\bthrips\b", r"\bhopper\b", r"\bcaterpillar\b", r"\binsecticide\b", r"\bchlorpyriphos\b",
        r"\bimidacloprid\b", r"\bspinosad\b", r"\bneem\b", r"\bpheromone\b", r"\betl\b"
    ],
    "Fertilizer & Nutrition": [
        r"\bfertilizer\b", r"\bnutrient\b", r"\bnpk\b", r"\bnitrogen\b", r"\bphosphorus\b",
        r"\bpotash\b", r"\bpotassium\b", r"\burea\b", r"\bdap\b", r"\bmop\b", r"\bzinc\b",
        r"\bmicronutrient\b", r"\bfym\b", r"\bmanure\b", r"\bdeficiency\b", r"\bkg/ha\b"
    ],
    "Weed Management": [
        r"\bweed\b", r"\bherbicide\b", r"\bphalaris\b", r"\bconvolvulus\b", r"\bchenopodium\b",
        r"\bisoproturon\b", r"\bsulfosulfuron\b", r"\bclodinafop\b", r"\b2,4-d\b", r"\bpendimethalin\b"
    ],
    "Seed Rate & Sowing": [
        r"\bseed rate\b", r"\bsowing\b", r"\bspacing\b", r"\bseed treatment\b", r"\bgermination\b",
        r"\bdrill\b", r"\bbroadcasting\b", r"\bplanting date\b", r"\btransplanting\b", r"\bkg/acre\b"
    ],
    "Irrigation & Water": [
        r"\birrigation\b", r"\bwater\b", r"\bcritical stage\b", r"\bcri stage\b", r"\bdrip\b",
        r"\bsprinkler\b", r"\bmoisture\b", r"\bdrainage\b"
    ],
    "Varietal Selection": [
        r"\bvariety\b", r"\bvarieties\b", r"\bhybrid\b", r"\bcultivar\b", r"\byield\b",
        r"\bmaturity\b", r"\bhd \d+\b", r"\bpbw \d+\b", r"\bpusa\b"
    ],
    "Harvesting & Storage": [
        r"\bharvest\b", r"\bthreshing\b", r"\bstorage\b", r"\bmoisture content\b", r"\bpost-harvest\b"
    ]
}

class AgronomicTagger:
    @staticmethod
    def extract_tags(text: str) -> Tuple[List[str], List[str], str]:
        """
        Extract crop tags, topic tags, and dominant language from text.
        """
        text_lower = text.lower()

        # 1. Identify Crops
        crop_tags = []
        for crop_name, patterns in CROP_DICTIONARY.items():
            if any(re.search(pat, text_lower) for pat in patterns):
                crop_tags.append(crop_name)

        # 2. Identify Topics
        topic_tags = []
        for topic_name, patterns in TOPIC_DICTIONARY.items():
            if any(re.search(pat, text_lower) for pat in patterns):
                topic_tags.append(topic_name)

        # 3. Detect Language (Simple Devanagari detection)
        # Devanagari Unicode block: \u0900-\u097F
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
        total_alpha = len(re.findall(r"[a-zA-Z\u0900-\u097F]", text))
        
        language = "en"
        if total_alpha > 0 and (devanagari_chars / total_alpha) > 0.4:
            language = "hi"

        return crop_tags, topic_tags, language
