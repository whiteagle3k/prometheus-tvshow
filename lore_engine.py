import os
import re
from pathlib import Path

class LoreEngine:
    _instance = None
    
    def __new__(cls, lore_file_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, lore_file_path=None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.lore_file_path = lore_file_path or os.environ.get('LORE_MD_PATH') or str(Path(__file__).parent / 'lore.md')
        self._raw = ''
        self.lore_data = {}
        self._load_and_parse()

    def _load_and_parse(self):
        try:
            with open(self.lore_file_path, 'r', encoding='utf-8') as f:
                self._raw = f.read()
            self._parse_world()
            self._parse_characters()
            self._parse_glossary()
            self._parse_themes()
            self._parse_arcs()
        except Exception as e:
            print(f"[LoreEngine] Error loading lore: {e}")

    def _parse_world(self):
        self.lore_data['world'] = {}
        # World Name
        m = re.search(r'### World Name\n(.+)', self._raw)
        self.lore_data['world']['name'] = m.group(1).strip() if m else None
        # Law of Emergence
        m = re.search(r'\*\*Law of Emergence\*\*:\s*\n"([^"]+)"', self._raw)
        self.lore_data['world']['law_of_emergence'] = m.group(1).strip() if m else None

    def _parse_characters(self):
        self.lore_data['characters'] = {}
        # Parse markdown table for characters - more flexible pattern
        m = re.search(r'\| Name\s*\| Dream[^\n]*\n\|[-| ]+\n((?:\|.+\n)+)', self._raw)
        if not m:
            return
        table = m.group(1).strip().split('\n')
        for row in table:
            cols = [c.strip() for c in row.strip('|').split('|')]
            if len(cols) >= 3:  # At least name, dream, traits
                name = cols[0]
                dream = cols[1]
                traits = cols[2]
                role = cols[3] if len(cols) > 3 else ""
                self.lore_data['characters'][name.lower()] = {
                    'name': name,
                    'dream': dream,
                    'traits': [t.strip() for t in traits.split(',')],
                    'role': role
                }

    def _parse_glossary(self):
        self.lore_data['glossary'] = {}
        m = re.search(r'## V. Terminology(.+?)##', self._raw, re.DOTALL)
        if not m:
            return
        glossary_section = m.group(1)
        for row in re.findall(r'\| ([^|]+)\| ([^|]+)\|', glossary_section):
            term, desc = row
            self.lore_data['glossary'][term.strip()] = desc.strip()

    def _parse_themes(self):
        self.lore_data['themes'] = []
        m = re.search(r'## VI. Themes(.+?)##', self._raw, re.DOTALL)
        if not m:
            return
        self.lore_data['themes'] = [line.strip('- ').strip() for line in m.group(1).split('\n') if line.strip('- ').strip()]

    def _parse_arcs(self):
        self.lore_data['arcs'] = []
        m = re.search(r'## VII\. Canonical Narrative Hooks(.+?)(?:##|$)', self._raw, re.DOTALL)
        if not m:
            return
        arc_lines = [line.strip('- ').strip() for line in m.group(1).split('\n') if line.strip('- ').strip()]
        for line in arc_lines:
            if '—' in line:
                title, description = line.split('—', 1)
                self.lore_data['arcs'].append({
                    'title': title.strip('* '),
                    'description': description.strip()
                })

    # --- API Methods ---
    def get_core_dream(self, character_id):
        c = self.lore_data['characters'].get(character_id.lower())
        return c['dream'] if c else None

    def get_traits(self, character_id):
        c = self.lore_data['characters'].get(character_id.lower())
        return c['traits'] if c else None

    def get_world_name(self):
        return self.lore_data['world'].get('name')

    def get_law_of_emergence(self):
        return self.lore_data['world'].get('law_of_emergence')

    def get_glossary_term(self, term):
        return self.lore_data['glossary'].get(term)

    def get_arc(self, title):
        for arc in self.lore_data['arcs']:
            if title.lower() in arc['title'].lower():
                return arc
        return None

    def list_all_arcs(self):
        return self.lore_data['arcs']

    def get_theme_statements(self):
        return self.lore_data['themes']

# Singleton
lore = LoreEngine() 