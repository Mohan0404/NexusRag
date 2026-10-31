"""
Verification script to count all components, questions, diagrams, and cards in the generated handbook.
"""
import os
import sys
import re

sys.path.insert(0, r"D:\Academic-Projects\RAG\scratch")

import build_full_handbook as base_builder
import sections_part1 as p1
import sections_part2 as p2
import sections_part3 as p3
import sections_part4 as p4
import sections_part5 as p5
import sections_part6 as p6
import sections_part7 as p7
import sections_part8 as p8

DOCS_DIR = r"D:\Academic-Projects\RAG\docs\interview"
NEXUS_DIR = r"D:\Academic-Projects\RAG\NexusRag\docs\interview"
MD_SOURCE = os.path.join(NEXUS_DIR, "GENWORX_RAG_INTERVIEW_PREPARATION.md")

md_text = base_builder.load_file(MD_SOURCE)

part1_html = p1.generate_part_1(base_builder)
part2_html = p2.generate_part_2(base_builder)
part3_html = p3.generate_part_3(base_builder)
part4_html = p4.generate_part_4(base_builder)
part5_html = p5.generate_part_5(base_builder)
part6_html = p6.generate_part_6(base_builder)
part7_html = p7.generate_part_7(base_builder)
part8_html = p8.generate_part_8(base_builder, md_text)

all_html = "\n".join([part1_html, part2_html, part3_html, part4_html, part5_html, part6_html, part7_html, part8_html])

# Counts
diagram_boxes = re.findall(r'class="diagram-box', all_html)
decision_cards = re.findall(r'class="decision-card', all_html)
tradeoff_cards = re.findall(r'class="tradeoff-card', all_html)
user_story_cards = re.findall(r'class="user-story-card', all_html)
code_cards = re.findall(r'class="code-card', all_html)
callouts = re.findall(r'class="callout', all_html)
stat_cards = re.findall(r'class="stat-card', all_html)
interview_cards = re.findall(r'class="interview-card', all_html)
section_headers = re.findall(r'class="section-header', all_html)
part_dividers = re.findall(r'class="part-divider', all_html)

# Extract Why and What-If questions from HTML or Part 8
whys = re.findall(r'class="why-def-card', all_html)
whatifs = re.findall(r'class="scenario-card', all_html)
rapid_fire = re.findall(r'class="rapid-fire-item', all_html)

print("=== VERIFIED HANDBOOK COMPONENT COUNTS ===")
print(f"Major Parts (Dividers): {len(part_dividers)}")
print(f"Numbered Technical Sections: {len(section_headers)}")
print(f"Architecture & Flow Diagrams: {len(diagram_boxes)}")
print(f"Decision Cards (Why Tech): {len(decision_cards)}")
print(f"Trade-Off Cards: {len(tradeoff_cards)}")
print(f"User Story Cards: {len(user_story_cards)}")
print(f"Code Cards (with Interviewer Q&A): {len(code_cards)}")
print(f"Callouts: {len(callouts)}")
print(f"Stat Cards: {len(stat_cards)}")
print(f"Categorized Interview Q&A Cards: {len(interview_cards)}")
print(f"Why Architectural Defenses: {len(whys)}")
print(f"What-If Failure Scenarios: {len(whatifs)}")
print(f"Rapid-Fire Cheat Items: {len(rapid_fire)}")
total_qa = len(interview_cards) + len(whys) + len(whatifs) + len(rapid_fire)
print(f"Total Interview Defense Items: {total_qa}")
