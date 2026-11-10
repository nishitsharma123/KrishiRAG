import os
import pymupdf
from PIL import Image, ImageDraw
import io

def create_agricultural_pdfs():
    output_dir = "./data/raw"
    os.makedirs(output_dir, exist_ok=True)

    # =========================================================================
    # PDF 1: ICAR Package of Practices for Wheat 2024
    # =========================================================================
    doc1 = pymupdf.open()

    # Page 1
    p1 = doc1.new_page(width=595, height=842)
    p1.insert_text((50, 70), "ICAR Package of Practices for Wheat Cultivation (NWPZ)", fontsize=16, fontname="helv", color=(0, 0.4, 0))
    p1.insert_text((50, 100), "Publishing Authority: Indian Council of Agricultural Research (ICAR-IIWBR)", fontsize=10, fontname="helv", color=(0.3, 0.3, 0.3))
    p1.insert_text((50, 130), "Section 1: Agro-Climatic Zones & Land Preparation", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_p1 = (
        "The North-Western Plains Zone (NWPZ) encompasses Punjab, Haryana, Delhi, Rajasthan, and Western Uttar Pradesh. "
        "Wheat (Triticum aestivum L.) is the predominant cereal crop of the Rabi season in this tract. "
        "Wheat thrives best in well-drained fertile loamy to clay loam soils with a pH ranging between 6.5 and 7.5.\n\n"
        "Land Preparation:\n"
        "1. For conventional tillage: Disc ploughing followed by 2-3 cultivations with cultivator and planking to create a firm, fine seedbed.\n"
        "2. For conservation agriculture: Zero-till seed-cum-fertilizer drill or Happy Seeder should be used directly in standing rice stubbles.\n"
        "Laser land levelling is recommended every 3 years to ensure uniform moisture distribution and save 20-25% irrigation water."
    )
    p1.insert_textbox(pymupdf.Rect(50, 150, 545, 450), body_p1, fontsize=10, fontname="helv", lineheight=1.4)
    p1.insert_text((270, 810), "- 1 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 2
    p2 = doc1.new_page(width=595, height=842)
    p2.insert_text((50, 70), "Section 2: Varietal Recommendations & Seed Rate", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_p2 = (
        "High-yielding wheat varieties approved for irrigated timely-sown conditions in NWPZ include:\n"
        "• HD 2967: Average yield 50.4 q/ha, resistant to brown rust, maturity 142 days.\n"
        "• HD 3086 (Pusa Gautami): Average yield 54.6 q/ha, superior chapati-making quality.\n"
        "• DBW 187 (Karan Vandana): Average yield 56.5 q/ha, highly resistant to stripe rust and leaf blight.\n"
        "• DBW 222 (Karan Narendra): Average yield 61.3 q/ha, heat-tolerant at terminal stage.\n"
        "• DBW 303 (Karan Vaishnavi): Average yield 81.2 q/ha under early sown high fertility conditions.\n\n"
        "Sowing Time & Seed Rate:\n"
        "Timely sown wheat should be planted between November 1 and November 15. "
        "The recommended seed rate for timely sown irrigated wheat is 100 kg/ha. "
        "For late sown conditions (December planting), increase seed rate to 125 kg/ha.\n\n"
        "Seed Treatment Protocol:\n"
        "Treat seed with Carboxin 37.5% + Thiram 37.5% (Vitavax Power) @ 2.5 g/kg seed to control loose smut and flag smut. "
        "In termite-endemic soils, treat seed with Chlorpyriphos 20% EC @ 4 ml/kg seed or Imidacloprid 600 FS @ 3 ml/kg seed before sowing."
    )
    p2.insert_textbox(pymupdf.Rect(50, 95, 545, 500), body_p2, fontsize=10, fontname="helv", lineheight=1.4)
    p2.insert_text((270, 810), "- 2 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 3
    p3 = doc1.new_page(width=595, height=842)
    p3.insert_text((50, 70), "Section 3: Nutrient & Fertilizer Dosage Schedule", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_p3 = (
        "Balanced fertilization is vital to obtain optimal grain yield and prevent lodging. "
        "The standard recommended fertilizer dosage for irrigated timely sown wheat in NWPZ is 150 kg N, 60 kg P2O5, and 40 kg K2O per hectare (150:60:40 kg/ha).\n\n"
        "Fertilizer Application Schedule:\n"
        "1. Basal Application: Apply full dose of Phosphorus (130 kg DAP/ha or 375 kg SSP/ha), full dose of Potash (67 kg MOP/ha), and 1/3rd of Nitrogen (55 kg Urea/ha) at the time of sowing.\n"
        "2. First Top Dressing: Apply 1/3rd Nitrogen (55 kg Urea/ha) at first irrigation (CRI stage, 21-25 days after sowing).\n"
        "3. Second Top Dressing: Apply remaining 1/3rd Nitrogen (55 kg Urea/ha) at second irrigation (Tillering/jointing stage, 40-45 DAS).\n\n"
        "Micronutrient Management:\n"
        "In zinc-deficient soils, apply Zinc Sulphate heptahydrate (21% Zn) @ 25 kg/ha at land preparation. "
        "If deficiency symptoms appear on standing crop (yellowing between leaf veins), spray 0.5% Zinc Sulphate (2.5 kg Zinc Sulphate + 1.25 kg unslaked lime in 500 litres of water per hectare).\n\n"
        "Irrigation Management:\n"
        "Crown Root Initiation (CRI) at 20-25 DAS is the most critical irrigation stage. Delaying irrigation at CRI reduces yield by up to 20-25%."
    )
    p3.insert_textbox(pymupdf.Rect(50, 95, 545, 520), body_p3, fontsize=10, fontname="helv", lineheight=1.4)
    p3.insert_text((270, 810), "- 3 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 4
    p4 = doc1.new_page(width=595, height=842)
    p4.insert_text((50, 70), "Section 4: Integrated Pest and Disease Management", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_p4 = (
        "Yellow Rust / Stripe Rust (Puccinia striiformis):\n"
        "Symptoms: Linear yellow to bright orange pustules arranged in parallel stripes on leaves.\n"
        "Control Measures:\n"
        "• Grow resistant varieties like DBW 187, DBW 222, and HD 3086.\n"
        "• As soon as the first foci of yellow rust are observed, spray Propiconazole 25% EC (Tilt) @ 0.1% (500 ml dissolved in 500 litres of water per hectare) or Tebuconazole 25.9% EC @ 500 ml/ha. Repeat the spray after 15 days if cloudy weather persists.\n\n"
        "Karnal Bunt (Tilletia indica):\n"
        "Spray Propiconazole 25% EC @ 500 ml/ha at 50% earhead emergence stage if humid and rainy conditions occur during flowering.\n\n"
        "Weed Management:\n"
        "For grassy weeds like Phalaris minor (Gulli danda) and Avena ludoviciana (Wild oat), spray Clodinafop-propargyl 15% WP @ 400 g/ha or Pinoxaden 5.1% EC @ 1000 ml/ha in 375-500 litres water at 30-35 DAS.\n"
        "For broadleaf weeds like Chenopodium album (Bathua), apply Metsulfuron-methyl 20% WP @ 20 g/ha or 2,4-D Ethyl Ester 38% EC @ 1250 ml/ha at 30-35 DAS."
    )
    p4.insert_textbox(pymupdf.Rect(50, 95, 545, 520), body_p4, fontsize=10, fontname="helv", lineheight=1.4)
    p4.insert_text((270, 810), "- 4 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    path1 = os.path.join(output_dir, "icar_wheat_package_of_practices_2024.pdf")
    doc1.save(path1)
    doc1.close()

    # =========================================================================
    # PDF 2: ICAR-NRRI Direct Seeded Rice (DSR) Management Guidelines
    # =========================================================================
    doc2 = pymupdf.open()

    # Page 1
    p1 = doc2.new_page(width=595, height=842)
    p1.insert_text((50, 70), "ICAR-NRRI Guidelines for Direct Seeded Rice (DSR)", fontsize=16, fontname="helv", color=(0, 0.4, 0))
    p1.insert_text((50, 100), "National Rice Research Institute (ICAR-NRRI), Cuttack", fontsize=10, fontname="helv", color=(0.3, 0.3, 0.3))
    p1.insert_text((50, 130), "Section 1: Agronomic Advantages & Land Levelling", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_d2_p1 = (
        "Direct Seeded Rice (DSR) is a resource-conserving technology that eliminates nursery raising, seedling uprooting, "
        "and puddled transplanting. DSR saves approximately 25-30% of irrigation water, requires 35-40% less labour, "
        "and shortens crop duration by 7-10 days, allowing timely planting of succeeding Rabi crops.\n\n"
        "Field Preparation:\n"
        "1. Precise Laser Levelling is mandatory to ensure uniform seed placement and prevent water stagnation.\n"
        "2. Stale Seedbed Technique: Irrigate the field 10-14 days prior to final sowing to encourage weed germination. "
        "Destroy the flush of germinated weed seedlings with non-selective herbicide Glyphosate 41% SL @ 2.5 litres/ha or Paraquat 24% SL @ 2.0 litres/ha."
    )
    p1.insert_textbox(pymupdf.Rect(50, 150, 545, 450), body_d2_p1, fontsize=10, fontname="helv", lineheight=1.4)
    p1.insert_text((270, 810), "- 1 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 2
    p2 = doc2.new_page(width=595, height=842)
    p2.insert_text((50, 70), "Section 2: Sowing Technique & Herbicide Weed Protocol", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_d2_p2 = (
        "Seed Rate and Sowing Technique:\n"
        "• Recommended seed rate for DSR is 20-25 kg/ha (compared to 40-50 kg in conventional transplanting).\n"
        "• Sowing depth must be maintained strictly at 2 to 3 cm using an inclined-plate DSR drill with press wheels.\n"
        "• Seed Treatment: Soak seeds in solution of Carbendazim 50% WP @ 2.0 g/kg seed or Trichoderma harzianum @ 10 g/kg seed.\n\n"
        "Weed Management (The Single Most Critical Factor in DSR):\n"
        "Weeds cause up to 60-80% yield loss in unmanaged direct-seeded rice. An integrated chemical regime is mandatory:\n"
        "1. Pre-emergence spray: Apply Pendimethalin 30% EC @ 1.0 kg a.i./ha (3.3 litres/ha) within 24 to 48 hours of sowing on moist soil.\n"
        "2. Early post-emergence spray: For grassy weeds and sedges at 15-20 DAS (2-3 leaf stage of weeds), spray Bispyribac-sodium 10% SC @ 200 ml/ha (25 g a.i./ha) dissolved in 375 litres of water.\n"
        "3. For broadleaf weeds and Cyperus: Apply Almix (Metsulfuron-methyl 10% + Chlorimuron-ethyl 10% WP) @ 20 g/ha mixed with 0.2% surfactant at 20-25 DAS."
    )
    p2.insert_textbox(pymupdf.Rect(50, 95, 545, 520), body_d2_p2, fontsize=10, fontname="helv", lineheight=1.4)
    p2.insert_text((270, 810), "- 2 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 3
    p3 = doc2.new_page(width=595, height=842)
    p3.insert_text((50, 70), "Section 3: Insect Pest & Disease Management in DSR", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_d2_p3 = (
        "Brown Plant Hopper (BPH - Nilaparvata lugens):\n"
        "Nymphs and adults congregate at the base of rice tillers, sucking sap and causing circular drying patches termed 'hopper burn'.\n"
        "Management:\n"
        "• Provide 'alley pathways' (30 cm gap every 2 meters) during line sowing to facilitate aeration and sunlight.\n"
        "• Avoid excessive application of urea nitrogen fertilizers.\n"
        "• Chemical spray directed at plant base: Spray Dinotefuran 20% SG @ 200 g/ha (40 g a.i./ha) or Pymetrozine 50% WDG @ 300 g/ha or Triflumezopyrim 10% SC @ 235 ml/ha in 500 litres of water per hectare.\n\n"
        "Bacterial Leaf Blight (BLB - Xanthomonas oryzae pv. oryzae):\n"
        "Symptoms: Water-soaked lesions progressing into wavy yellow-white stripes along leaf margins.\n"
        "Management: Drain excess water from the field. Avoid top-dressing of nitrogen. Spray Streptocycline (90% streptomycin sulphate + 10% tetracycline hydrochloride) @ 15 g mixed with Copper Oxychloride 50% WP @ 500 g in 500 litres of water per hectare."
    )
    p3.insert_textbox(pymupdf.Rect(50, 95, 545, 520), body_d2_p3, fontsize=10, fontname="helv", lineheight=1.4)
    p3.insert_text((270, 810), "- 3 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    path2 = os.path.join(output_dir, "icar_paddy_direct_seeded_rice_manual.pdf")
    doc2.save(path2)
    doc2.close()

    # =========================================================================
    # PDF 3: ICAR-DRMR Integrated Pest and Disease Management in Mustard
    # =========================================================================
    doc3 = pymupdf.open()

    # Page 1
    p1 = doc3.new_page(width=595, height=842)
    p1.insert_text((50, 70), "ICAR-DRMR Guidelines for IPM in Rapeseed-Mustard", fontsize=16, fontname="helv", color=(0, 0.4, 0))
    p1.insert_text((50, 100), "Directorate of Rapeseed-Mustard Research (ICAR-DRMR), Bharatpur", fontsize=10, fontname="helv", color=(0.3, 0.3, 0.3))
    p1.insert_text((50, 130), "Section 1: Mustard Aphid Biology & Economic Threshold", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_d3_p1 = (
        "Rapeseed-Mustard (Brassica juncea) is the premier oilseed crop of Indian agriculture during the Rabi season. "
        "The productivity of mustard is severely curtailed by insect pests and diseases, with mustard aphid causing up to 30-70% yield loss.\n\n"
        "Mustard Aphid (Lipaphis erysimi Kaltenbach):\n"
        "Aphids appear from December to February. Nymphs and adults suck cell sap from tender shoots, leaves, inflorescences, and pods. "
        "Excreted honeydew fosters black sooty mould growth, impairing photosynthesis.\n\n"
        "Economic Threshold Level (ETL):\n"
        "Chemical intervention should only be initiated when the pest population crosses the ETL:\n"
        "• 25 to 30 aphids per 10 cm central twig / terminal shoot, OR\n"
        "• 1.5 to 2.0 cm aphid colony length on 10-20% of sampled plants.\n"
        "Early sowing (between October 1 and October 15) enables the crop to escape peak aphid infestation in January."
    )
    p1.insert_textbox(pymupdf.Rect(50, 150, 545, 450), body_d3_p1, fontsize=10, fontname="helv", lineheight=1.4)
    p1.insert_text((270, 810), "- 1 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 2
    p2 = doc3.new_page(width=595, height=842)
    p2.insert_text((50, 70), "Section 2: Bio-Control & Pollinator-Safe Chemical Control", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_d3_p2 = (
        "Biological and Cultural Controls:\n"
        "• Conserve predatory ladybird beetles (Coccinella septempunctata, Menochilus sexmaculata). "
        "If ladybird beetle population is ≥ 1 beetle per plant, delay chemical spraying as natural bio-agents will suppress aphids.\n"
        "• Install yellow sticky traps @ 10-12 traps per hectare for early monitoring.\n\n"
        "Chemical Spray Protocol:\n"
        "When aphid population exceeds ETL, spray one of the following recommended insecticides:\n"
        "1. Dimethoate 30% EC (Rogor) @ 1.0 ml per litre of water (600-750 ml in 600-750 litres water/ha).\n"
        "2. Oxydemeton-methyl 25% EC (Metasystox) @ 1.0 ml per litre of water.\n"
        "3. Thiamethoxam 25% WG @ 0.2 g per litre of water (100 g in 500 litres water/ha).\n\n"
        "CRITICAL POLLINATOR SAFETY DIRECTIVE:\n"
        "Mustard is heavily cross-pollinated by honeybees (Apis cerana, Apis mellifera). "
        "Insecticide sprays must strictly be conducted during late afternoon (after 3:30 PM) when bee foraging activity ceases. "
        "Never spray during peak morning bloom hours to prevent mass pollinator mortality."
    )
    p2.insert_textbox(pymupdf.Rect(50, 95, 545, 520), body_d3_p2, fontsize=10, fontname="helv", lineheight=1.4)
    p2.insert_text((270, 810), "- 2 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    # Page 3
    p3 = doc3.new_page(width=595, height=842)
    p3.insert_text((50, 70), "Section 3: White Rust & Alternaria Blight Management", fontsize=13, fontname="helv", color=(0.1, 0.1, 0.1))
    
    body_d3_p3 = (
        "White Rust (Albugo candida):\n"
        "Symptoms: Prominent white or creamy pustules on the lower surface of leaves. Infection at flowering leads to malformation and hypertrophy of floral organs ('staghead' deformity).\n\n"
        "Management Strategy:\n"
        "• Seed Treatment: Treat seeds with Metalaxyl 35% WS (Apron) @ 6 g/kg seed to protect early seedling growth.\n"
        "• Foliar Spray: At 45-50 days after sowing or at first appearance of pustules, spray Mancozeb 75% WP @ 2.0 g/litre water (1.0 kg/ha in 500 L water) or Metalaxyl 8% + Mancozeb 64% WP (Ridomil MZ 72 WP) @ 2.0 g/litre water.\n"
        "• Repeat spray after 15-20 days if morning fog and high relative humidity (>80%) persist.\n\n"
        "Alternaria Black Spot (Alternaria brassicae):\n"
        "Spray Iprodione 50% WP @ 2.0 g/litre water or Mancozeb 75% WP @ 2.0 g/litre water. Collect and burn crop residues after threshing to eliminate resting spores."
    )
    p3.insert_textbox(pymupdf.Rect(50, 95, 545, 520), body_d3_p3, fontsize=10, fontname="helv", lineheight=1.4)
    p3.insert_text((270, 810), "- 3 -", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5))

    path3 = os.path.join(output_dir, "icar_mustard_integrated_pest_management.pdf")
    doc3.save(path3)
    doc3.close()

    # =========================================================================
    # PDF 4: Scanned Sample Page (contains drawing/image with < 50 chars text)
    # =========================================================================
    doc4 = pymupdf.open()
    p_scan = doc4.new_page(width=595, height=842)
    p_scan.insert_text((50, 50), "Plate 1", fontsize=10, fontname="helv") # < 50 chars
    
    # Generate a simple synthetic image and insert it
    img = Image.new("RGB", (400, 300), color=(240, 248, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 380, 280], outline=(34, 139, 34), width=3)
    d.text((40, 100), "ICAR SCAN ARTIFACT: PEST CHART", fill=(0, 100, 0))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    p_scan.insert_image(pymupdf.Rect(50, 100, 500, 450), stream=img_bytes)
    
    path4 = os.path.join(output_dir, "icar_scanned_specimen_page.pdf")
    doc4.save(path4)
    doc4.close()

    print(f"Generated 4 authentic ICAR test PDF documents under '{output_dir}':")
    print(f" 1. {path1} (4 pages)")
    print(f" 2. {path2} (3 pages)")
    print(f" 3. {path3} (3 pages)")
    print(f" 4. {path4} (1 scanned page)")

if __name__ == "__main__":
    create_agricultural_pdfs()
