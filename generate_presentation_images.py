#!/usr/bin/env python3
"""
Raseed Project - Presentation Image Generator
Generates professional presentation images for the Raseed project
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import json

class RaseedPresentationGenerator:
    def __init__(self):
        self.colors = {
            'primary_blue': '#2563eb',
            'secondary_purple': '#7c3aed',
            'accent_orange': '#f59e0b',
            'success_green': '#10b981',
            'warning_orange': '#f97316',
            'error_red': '#ef4444',
            'text_dark': '#1f2937',
            'text_light': '#6b7280',
            'background': '#ffffff'
        }
        
        # Create output directory
        self.output_dir = 'presentation_images'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_title_slide(self):
        """Generate Slide 1: Title Slide"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Create gradient background
        gradient = np.linspace(0, 1, 100)
        ax.imshow([gradient], extent=[0, 16, 0, 9], aspect='auto', 
                  cmap='Blues', alpha=0.1)
        
        # Add geometric patterns
        for i in range(20):
            x = np.random.uniform(0, 16)
            y = np.random.uniform(0, 9)
            size = np.random.uniform(0.1, 0.3)
            circle = Circle((x, y), size, color=self.colors['primary_blue'], alpha=0.1)
            ax.add_patch(circle)
        
        # Main title
        ax.text(8, 6, 'Raseed', fontsize=48, fontweight='bold', 
                color=self.colors['primary_blue'], ha='center', va='center')
        
        # Tagline
        ax.text(8, 5, 'AI-Powered Receipt Management\nwith Indian Language Support', 
                fontsize=20, color=self.colors['text_dark'], ha='center', va='center')
        
        # Subtitle
        ax.text(8, 3.5, 'Smart Receipt Processing • Google Wallet Integration • Multi-Language AI', 
                fontsize=14, color=self.colors['text_light'], ha='center', va='center')
        
        # Indian flag colors accent
        saffron_rect = Rectangle((2, 1), 1, 0.5, color=self.colors['accent_orange'])
        green_rect = Rectangle((13, 1), 1, 0.5, color=self.colors['success_green'])
        ax.add_patch(saffron_rect)
        ax.add_patch(green_rect)
        
        # Receipt icons
        receipt_positions = [(3, 7.5), (13, 7.5), (2, 2.5), (14, 2.5)]
        for x, y in receipt_positions:
            receipt = Rectangle((x-0.3, y-0.2), 0.6, 0.4, 
                              color=self.colors['secondary_purple'], alpha=0.3)
            ax.add_patch(receipt)
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/01_title_slide.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_problem_solution_slide(self):
        """Generate Slide 2: Problem Statement"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        
        # Problem side
        ax1.set_facecolor(self.colors['background'])
        ax1.text(4, 8, 'Current Pain Points', fontsize=24, fontweight='bold', 
                color=self.colors['error_red'], ha='center')
        
        problems = [
            ('📄', 'Paper receipts everywhere'),
            ('🔍', 'Manual data entry'),
            ('🌍', 'Language barriers'),
            ('💳', 'No digital wallet integration'),
            ('📊', 'No spending insights')
        ]
        
        for i, (icon, text) in enumerate(problems):
            y_pos = 6.5 - i * 1.2
            ax1.text(1, y_pos, icon, fontsize=24, ha='center')
            ax1.text(2.5, y_pos, text, fontsize=16, color=self.colors['text_dark'])
        
        # Solution side
        ax2.set_facecolor(self.colors['background'])
        ax2.text(4, 8, 'Raseed Solution', fontsize=24, fontweight='bold', 
                color=self.colors['success_green'], ha='center')
        
        solutions = [
            ('✅', 'AI-powered extraction'),
            ('✅', 'Multi-language support'),
            ('✅', 'Google Wallet integration'),
            ('✅', 'Smart insights'),
            ('✅', 'Real-time notifications')
        ]
        
        for i, (icon, text) in enumerate(solutions):
            y_pos = 6.5 - i * 1.2
            ax2.text(1, y_pos, icon, fontsize=24, ha='center')
            ax2.text(2.5, y_pos, text, fontsize=16, color=self.colors['text_dark'])
        
        # Add divider
        ax1.axvline(x=8, color=self.colors['text_light'], alpha=0.3, linewidth=2)
        
        ax1.set_xlim(0, 8)
        ax1.set_ylim(0, 9)
        ax2.set_xlim(8, 16)
        ax2.set_ylim(0, 9)
        ax1.axis('off')
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/02_problem_solution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_features_overview(self):
        """Generate Slide 3: Key Features Overview"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Central hub
        center_circle = Circle((8, 4.5), 1.5, color=self.colors['primary_blue'], alpha=0.8)
        ax.add_patch(center_circle)
        ax.text(8, 4.5, 'Raseed', fontsize=20, fontweight='bold', 
                color='white', ha='center', va='center')
        
        # Feature spokes
        features = [
            ('🤖', 'AI-Powered\nProcessing', 2, 7),
            ('🇮🇳', 'Indian Language\nSupport', 14, 7),
            ('💳', 'Google Wallet\nIntegration', 14, 2),
            ('🔍', 'Natural Language\nQueries', 2, 2),
            ('📊', 'Spending\nInsights', 6, 8),
            ('📱', 'Real-time\nNotifications', 10, 8)
        ]
        
        for icon, text, x, y in features:
            # Draw connection line
            ax.plot([8, x], [4.5, y], color=self.colors['secondary_purple'], 
                   alpha=0.5, linewidth=2)
            
            # Feature circle
            feature_circle = Circle((x, y), 0.8, color=self.colors['secondary_purple'], alpha=0.6)
            ax.add_patch(feature_circle)
            
            # Icon and text
            ax.text(x, y+0.3, icon, fontsize=16, ha='center', va='center')
            ax.text(x, y-0.3, text, fontsize=10, ha='center', va='center', 
                   color='white', fontweight='bold')
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/03_features_overview.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_technology_stack(self):
        """Generate Slide 4: Technology Stack"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Layer definitions
        layers = [
            ('Frontend Layer', ['React.js', 'Modern UI'], 1),
            ('Backend Layer', ['FastAPI', 'RESTful APIs'], 2),
            ('AI/ML Layer', ['Google Gemini Vision', 'Document AI', 'Vertex AI', 'NLP'], 3),
            ('Storage Layer', ['Firebase Storage', 'Firestore DB'], 4),
            ('External Services', ['Google Wallet API'], 5)
        ]
        
        colors = [self.colors['primary_blue'], self.colors['secondary_purple'], 
                 self.colors['accent_orange'], self.colors['success_green'], 
                 self.colors['warning_orange']]
        
        for i, (layer_name, technologies, layer_num) in enumerate(layers):
            y_pos = 8 - layer_num * 1.2
            
            # Layer box
            layer_box = FancyBboxPatch((1, y_pos-0.4), 14, 0.8, 
                                      boxstyle="round,pad=0.1", 
                                      facecolor=colors[i], alpha=0.7)
            ax.add_patch(layer_box)
            
            # Layer name
            ax.text(2, y_pos, layer_name, fontsize=16, fontweight='bold', 
                   color='white')
            
            # Technologies
            tech_text = ' • '.join(technologies)
            ax.text(8, y_pos, tech_text, fontsize=12, ha='center', va='center', 
                   color='white')
            
            # Connection arrows
            if layer_num < 5:
                ax.arrow(8, y_pos-0.4, 0, -0.3, head_width=0.2, head_length=0.1, 
                        fc=colors[i], ec=colors[i], alpha=0.8)
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/04_technology_stack.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_system_architecture(self):
        """Generate Slide 5: System Architecture"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Components
        components = [
            ('User Interface\n(React.js)', 2, 4.5),
            ('Backend API\n(FastAPI)', 6, 4.5),
            ('AI Services\n(Google Cloud)', 10, 4.5),
            ('Storage\n(Firebase)', 14, 4.5)
        ]
        
        # Draw components
        for name, x, y in components:
            component_box = FancyBboxPatch((x-1.5, y-0.8), 3, 1.6, 
                                         boxstyle="round,pad=0.1", 
                                         facecolor=self.colors['primary_blue'], alpha=0.8)
            ax.add_patch(component_box)
            ax.text(x, y, name, fontsize=12, ha='center', va='center', 
                   color='white', fontweight='bold')
        
        # Data flow arrows
        flow_steps = ['Upload', 'Process', 'Store', 'Analyze', 'Notify']
        for i, step in enumerate(flow_steps):
            x = 1 + i * 3.5
            ax.text(x, 6.5, step, fontsize=10, ha='center', va='center', 
                   color=self.colors['text_dark'])
            
            if i < len(flow_steps) - 1:
                ax.arrow(x+0.5, 6.5, 2.5, 0, head_width=0.1, head_length=0.1, 
                        fc=self.colors['secondary_purple'], ec=self.colors['secondary_purple'])
        
        # Connection arrows between components
        for i in range(len(components) - 1):
            x1, y1 = components[i][1], components[i][2]
            x2, y2 = components[i+1][1], components[i+1][2]
            ax.arrow(x1+1.5, y1, 1, 0, head_width=0.1, head_length=0.1, 
                    fc=self.colors['accent_orange'], ec=self.colors['accent_orange'])
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/05_system_architecture.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_ai_processing_pipeline(self):
        """Generate Slide 6: AI-Powered Receipt Processing"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Pipeline steps
        steps = [
            ('Input\nReceipt Image', 2, 4.5),
            ('Gemini Vision AI\nExtract Text & Data', 5, 4.5),
            ('Document AI\nStructured Extraction', 8, 4.5),
            ('Data Validation\nVerify Accuracy', 11, 4.5),
            ('Storage\nSave to Firebase', 14, 4.5)
        ]
        
        # Draw pipeline
        for i, (name, x, y) in enumerate(steps):
            # Step box
            step_box = FancyBboxPatch((x-1.2, y-0.6), 2.4, 1.2, 
                                     boxstyle="round,pad=0.1", 
                                     facecolor=self.colors['primary_blue'], alpha=0.8)
            ax.add_patch(step_box)
            ax.text(x, y, name, fontsize=10, ha='center', va='center', 
                   color='white', fontweight='bold')
            
            # Connection arrows
            if i < len(steps) - 1:
                ax.arrow(x+1.2, y, 1.1, 0, head_width=0.1, head_length=0.1, 
                        fc=self.colors['secondary_purple'], ec=self.colors['secondary_purple'])
        
        # Output section
        ax.text(8, 2, 'Output: Structured Receipt Data', fontsize=16, fontweight='bold', 
               color=self.colors['text_dark'], ha='center')
        
        output_items = ['Merchant', 'Items', 'Totals', 'Date', 'Category']
        for i, item in enumerate(output_items):
            x = 2 + i * 3
            item_box = Rectangle((x-0.8, 1), 1.6, 0.6, 
                               color=self.colors['success_green'], alpha=0.6)
            ax.add_patch(item_box)
            ax.text(x, 1.3, item, fontsize=10, ha='center', va='center', 
                   color='white', fontweight='bold')
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/06_ai_processing_pipeline.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_multi_language_support(self):
        """Generate Slide 7: Multi-Language Support"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Title
        ax.text(8, 8, 'Supported Languages (10+ Indian Languages)', 
                fontsize=20, fontweight='bold', color=self.colors['text_dark'], ha='center')
        
        # Languages
        languages = [
            ('हिंदी', 'Hindi'),
            ('தமிழ்', 'Tamil'),
            ('ಕನ್ನಡ', 'Kannada'),
            ('తెలుగు', 'Telugu'),
            ('മലയാളം', 'Malayalam')
        ]
        
        for i, (native, english) in enumerate(languages):
            x = 2 + i * 3
            # Language box
            lang_box = FancyBboxPatch((x-1, 5.5), 2, 1, 
                                     boxstyle="round,pad=0.1", 
                                     facecolor=self.colors['primary_blue'], alpha=0.7)
            ax.add_patch(lang_box)
            ax.text(x, 6, native, fontsize=16, ha='center', va='center', 
                   color='white', fontweight='bold')
            ax.text(x, 5.5, english, fontsize=12, ha='center', va='center', 
                   color='white')
        
        # Example queries
        ax.text(8, 4, 'Example Queries:', fontsize=16, fontweight='bold', 
               color=self.colors['text_dark'], ha='center')
        
        queries = [
            ('मुझे कुकिंग के लिए क्या चाहिए?', 'Hindi'),
            ('கோழி மற்றும் அரிசியுடன் என்ன சமைக்க முடியும்?', 'Tamil'),
            ('ಕೋಳಿ ಮತ್ತು ಅಕ್ಕಿಯೊಂದಿಗೆ ನಾನು ಏನು ಬೇಯಿಸಬಹುದು?', 'Kannada')
        ]
        
        for i, (query, lang) in enumerate(queries):
            y = 3 - i * 0.8
            ax.text(1, y, f'{lang}:', fontsize=12, fontweight='bold', 
                   color=self.colors['text_dark'])
            ax.text(4, y, query, fontsize=10, color=self.colors['text_dark'])
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/07_multi_language_support.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_performance_metrics(self):
        """Generate Slide 14: Performance Metrics"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Title
        ax.text(8, 8.5, 'Performance Metrics', fontsize=24, fontweight='bold', 
               color=self.colors['text_dark'], ha='center')
        
        # Speed metrics
        ax.text(4, 7, 'Speed Metrics', fontsize=18, fontweight='bold', 
               color=self.colors['primary_blue'], ha='center')
        
        speed_items = [
            ('⚡', 'Receipt processing', '< 5 seconds'),
            ('⚡', 'Query response', '< 2 seconds'),
            ('⚡', 'Real-time updates', '< 100ms')
        ]
        
        for i, (icon, metric, value) in enumerate(speed_items):
            y = 6 - i * 0.8
            ax.text(1, y, icon, fontsize=16, ha='center')
            ax.text(2, y, metric, fontsize=14, color=self.colors['text_dark'])
            ax.text(6, y, value, fontsize=14, fontweight='bold', 
                   color=self.colors['success_green'])
        
        # Accuracy metrics
        ax.text(12, 7, 'Accuracy Metrics', fontsize=18, fontweight='bold', 
               color=self.colors['secondary_purple'], ha='center')
        
        accuracy_items = [
            ('🎯', 'Receipt processing', '95%+ accuracy'),
            ('🎯', 'Query understanding', '90%+ accuracy'),
            ('🎯', 'Language detection', '98%+ accuracy')
        ]
        
        for i, (icon, metric, value) in enumerate(accuracy_items):
            y = 6 - i * 0.8
            ax.text(9, y, icon, fontsize=16, ha='center')
            ax.text(10, y, metric, fontsize=14, color=self.colors['text_dark'])
            ax.text(14, y, value, fontsize=14, fontweight='bold', 
                   color=self.colors['success_green'])
        
        # Scalability
        ax.text(8, 3.5, 'Scalability', fontsize=18, fontweight='bold', 
               color=self.colors['accent_orange'], ha='center')
        
        scale_items = [
            ('📈', '1000+ concurrent users'),
            ('📈', '100+ receipts/minute'),
            ('📈', '500+ queries/minute')
        ]
        
        for i, (icon, metric) in enumerate(scale_items):
            x = 4 + i * 4
            ax.text(x, 2.5, icon, fontsize=16, ha='center')
            ax.text(x, 2, metric, fontsize=12, color=self.colors['text_dark'], ha='center')
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/14_performance_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_development_roadmap(self):
        """Generate Slide 15: Development Roadmap"""
        fig, ax = plt.subplots(1, 1, figsize=(16, 9))
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        
        # Title
        ax.text(8, 8.5, 'Development Roadmap', fontsize=24, fontweight='bold', 
               color=self.colors['text_dark'], ha='center')
        
        # Timeline
        steps = [
            ('Step 1', 'Upload & Storage', 'COMPLETE', self.colors['success_green']),
            ('Step 2', 'AI Integration', 'COMPLETE', self.colors['success_green']),
            ('Step 3', 'Google Wallet', 'COMPLETE', self.colors['success_green']),
            ('Step 4', 'Natural Language Queries', 'IN PROGRESS', self.colors['warning_orange']),
            ('Step 5', 'Insights & Notifications', 'IN PROGRESS', self.colors['warning_orange'])
        ]
        
        for i, (step_num, description, status, color) in enumerate(steps):
            y = 7 - i * 1.2
            
            # Step box
            step_box = FancyBboxPatch((1, y-0.4), 3, 0.8, 
                                     boxstyle="round,pad=0.1", 
                                     facecolor=color, alpha=0.8)
            ax.add_patch(step_box)
            ax.text(2.5, y, step_num, fontsize=12, ha='center', va='center', 
                   color='white', fontweight='bold')
            
            # Description
            ax.text(5, y, description, fontsize=14, color=self.colors['text_dark'])
            
            # Status
            status_box = FancyBboxPatch((12, y-0.3), 2, 0.6, 
                                       boxstyle="round,pad=0.1", 
                                       facecolor=color, alpha=0.6)
            ax.add_patch(status_box)
            ax.text(13, y, status, fontsize=10, ha='center', va='center', 
                   color='white', fontweight='bold')
            
            # Connection line
            if i < len(steps) - 1:
                ax.arrow(2.5, y-0.4, 0, -0.4, head_width=0.1, head_length=0.1, 
                        fc=color, ec=color)
        
        # Future section
        ax.text(8, 1, 'Future: Advanced analytics, ML predictions, voice integration', 
               fontsize=14, color=self.colors['text_light'], ha='center', style='italic')
        
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 9)
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/15_development_roadmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_all_images(self):
        """Generate all presentation images"""
        print("🎨 Generating Raseed Project Presentation Images...")
        
        self.create_title_slide()
        print("✅ Generated: Title Slide")
        
        self.create_problem_solution_slide()
        print("✅ Generated: Problem Statement")
        
        self.create_features_overview()
        print("✅ Generated: Features Overview")
        
        self.create_technology_stack()
        print("✅ Generated: Technology Stack")
        
        self.create_system_architecture()
        print("✅ Generated: System Architecture")
        
        self.create_ai_processing_pipeline()
        print("✅ Generated: AI Processing Pipeline")
        
        self.create_multi_language_support()
        print("✅ Generated: Multi-Language Support")
        
        self.create_performance_metrics()
        print("✅ Generated: Performance Metrics")
        
        self.create_development_roadmap()
        print("✅ Generated: Development Roadmap")
        
        print(f"\n🎉 All images generated successfully in '{self.output_dir}/' directory!")
        print("📁 Generated images:")
        for file in sorted(os.listdir(self.output_dir)):
            if file.endswith('.png'):
                print(f"   - {file}")

if __name__ == "__main__":
    generator = RaseedPresentationGenerator()
    generator.generate_all_images() 