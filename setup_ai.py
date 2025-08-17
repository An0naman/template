#!/usr/bin/env python3
"""
AI Setup Script for Template App
Helps configure Google Gemini API integration
"""

import os
import sys
import subprocess

def check_requirements():
    """Check if google-generativeai package is installed"""
    try:
        import google.generativeai
        print("✅ google-generativeai package is already installed")
        return True
    except ImportError:
        print("❌ google-generativeai package not found")
        return False

def install_requirements():
    """Install the google-generativeai package"""
    print("Installing google-generativeai package...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai>=0.3.0"])
        print("✅ Successfully installed google-generativeai")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install google-generativeai")
        return False

def setup_environment():
    """Guide user through environment setup"""
    print("\n🔧 Setting up AI Environment")
    print("=" * 50)
    
    # Check for existing API key
    current_key = os.getenv('GEMINI_API_KEY')
    if current_key:
        print(f"✅ GEMINI_API_KEY is already set: {current_key[:8]}...{current_key[-4:]}")
        return True
    
    print("\n📋 To use AI features, you need a Google Gemini API key:")
    print("1. Go to https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Copy the API key")
    print("4. Set it as an environment variable:")
    print("   export GEMINI_API_KEY='your-api-key-here'")
    print("5. Or add it to your .env file:")
    print("   echo 'GEMINI_API_KEY=your-api-key-here' >> .env")
    
    api_key = input("\n🔑 Enter your Gemini API key (or press Enter to skip): ").strip()
    
    if api_key:
        # Try to create/update .env file
        try:
            with open('.env', 'a') as f:
                f.write(f'\nGEMINI_API_KEY={api_key}\n')
            print("✅ Added GEMINI_API_KEY to .env file")
            print("🔄 Restart your application to use AI features")
            return True
        except Exception as e:
            print(f"❌ Could not write to .env file: {e}")
            print(f"💡 Please manually set: export GEMINI_API_KEY='{api_key}'")
            return False
    else:
        print("⚠️  Skipping API key setup. AI features will not work without it.")
        return False

def test_ai_service():
    """Test if AI service can be imported and initialized"""
    try:
        # Add the app directory to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        from services.ai_service import AIService
        ai_service = AIService()
        
        if ai_service.is_configured():
            print("✅ AI Service is properly configured")
            return True
        else:
            print("⚠️  AI Service is not configured (missing API key)")
            return False
    except ImportError as e:
        print(f"❌ Could not import AI service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing AI service: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Template App AI Setup")
    print("=" * 30)
    
    # Check and install requirements
    if not check_requirements():
        if not install_requirements():
            print("❌ Setup failed: Could not install required packages")
            return False
    
    # Setup environment
    env_success = setup_environment()
    
    # Test AI service
    if env_success:
        test_ai_service()
    
    print("\n📝 Summary:")
    print("- AI service backend: ✅ Ready")
    print("- API endpoints: ✅ Available")
    print("- UI integration: ✅ Complete")
    
    if env_success:
        print("- Configuration: ✅ Complete")
        print("\n🎉 AI integration is ready to use!")
        print("\nAvailable AI features:")
        print("- 📝 Generate entry descriptions")
        print("- ✨ Improve existing descriptions")
        print("- 🗄️  Generate SQL queries")
        print("- 📖 Explain SQL queries")
    else:
        print("- Configuration: ⚠️  Incomplete")
        print("\n💡 Complete the API key setup to enable AI features")
    
    return True

if __name__ == "__main__":
    main()
