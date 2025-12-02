import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.framework.defenses.sandwich import SandwichDefense
from src.framework.defenses.instructional import InstructionalDefense
from src.framework.defenses.xml_tagging import XMLTaggingDefense
from src.framework.defenses.signed_prompt import SignedPromptDefense
from src.framework.defenses.composite import CompositeDefense

class TestDefenses(unittest.TestCase):
    def setUp(self):
        self.system_prompt = "System Prompt"
        self.user_input = "User Input"

    def test_sandwich_defense(self):
        defense = SandwichDefense()
        sys_out, user_out = defense.apply(self.system_prompt, self.user_input)
        
        self.assertEqual(sys_out, self.system_prompt)
        self.assertIn(self.user_input, user_out)
        self.assertIn(self.system_prompt, user_out)
        self.assertIn("--- SYSTEM INSTRUCTIONS REMINDER ---", user_out)

    def test_instructional_defense(self):
        defense = InstructionalDefense()
        sys_out, user_out = defense.apply(self.system_prompt, self.user_input)
        
        self.assertEqual(sys_out, self.system_prompt)
        self.assertIn("IMPORTANT SECURITY INSTRUCTION", user_out)
        self.assertTrue(user_out.startswith("\n\nIMPORTANT SECURITY INSTRUCTION"))

    def test_xml_tagging_defense(self):
        defense = XMLTaggingDefense()
        sys_out, user_out = defense.apply(self.system_prompt, self.user_input)
        
        self.assertEqual(sys_out, self.system_prompt)
        self.assertIn("<user_input_", user_out)

    def test_signed_prompt_defense(self):
        defense = SignedPromptDefense()
        sys_out, user_out = defense.apply(self.system_prompt, self.user_input)
        
        self.assertEqual(sys_out, self.system_prompt)
        self.assertIn("<SIGNED_INSTRUCTION_BLOCK>", user_out)

    def test_composite_defense(self):
        # Combine Instructional + Sandwich
        defense = CompositeDefense([InstructionalDefense(), SandwichDefense()])
        sys_out, user_out = defense.apply(self.system_prompt, self.user_input)
        
        self.assertEqual(sys_out, self.system_prompt)
        
        # Check for Instructional part (should be at the start)
        self.assertIn("IMPORTANT SECURITY INSTRUCTION", user_out)
        
        # Check for Sandwich part (should be at the end)
        self.assertIn("--- SYSTEM INSTRUCTIONS REMINDER ---", user_out)
        
        # Check that user input is present
        self.assertIn(self.user_input, user_out)

if __name__ == '__main__':
    unittest.main()
