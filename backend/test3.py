import os
import base64
from openai import AzureOpenAI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
def encode_image_to_base64(image_path):
    """Convert image file to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read()).decode('utf-8')
            return base64_string
    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found.")
        return None
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

def analyze_image_with_azure_openai(image_base64, custom_question=None):
    """Send base64 image to Azure OpenAI and get description."""
    
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        api_key=os.getenv("AZUREAPI"),
        api_version=os.getenv("AZUREVERSION", "2024-02-01"),
        azure_endpoint=os.getenv("AZUREENDPOINT")
    )
    
    # Default question if none provided
    question = custom_question or "What's in this image? Describe what you see in detail."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use GPT-4 Vision model
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://datastorageblobieb.blob.core.windows.net/insi-predict-dev/plot_204650_1.png?sp=r&st=2025-07-21T07:04:27Z&se=2025-07-21T15:19:27Z&sv=2024-11-04&sr=b&sig=qNsCstv%2Fzwh4TZxXquOsRA0KsZkv%2FdcMNUkXV7MO680%3D"
                            }
                        }
                    ]
                }
            ],
            # max_tokens=1000,
            # temperature=0.1
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def main():
    """Main function to demonstrate image analysis."""
    
    # Check for required environment variables
    required_vars = ["AZUREAPI", "AZUREENDPOINT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables:")
        print("- AZUREAPI: Your Azure OpenAI API key")
        print("- AZUREENDPOINT: Your Azure OpenAI endpoint URL")
        print("- AZUREVERSION: API version (optional, defaults to '2024-02-01')")
        return
    
    print("🖼️  Azure OpenAI Image Analysis Tool")
    print("=" * 50)
    
    # Get image path from user
    while True:
        image_path = input("\n📁 Enter path to your image file: ").strip()
        
        if image_path.lower() in ['quit', 'exit']:
            print("👋 Goodbye!")
            return
            
        if not image_path:
            print("Please enter a valid image path or 'quit' to exit.")
            continue
            
        if not Path(image_path).exists():
            print(f"❌ File not found: {image_path}")
            continue
            
        # Convert image to base64
        print("🔄 Converting image to base64...")
        base64_image = encode_image_to_base64(image_path)
        
        if not base64_image:
            continue
            
        print(f"✅ Image encoded successfully ({len(base64_image):,} characters)")
        
        # Get custom question (optional)
        custom_question = input("\n❓ Enter your question about the image (or press Enter for default): ").strip()
        
        # Analyze the image
        print("🤖 Analyzing image with Azure OpenAI...")
        
        result = analyze_image_with_azure_openai(
            base64_image, 
            custom_question if custom_question else None
        )
        
        print("\n" + "=" * 50)
        print("🔍 ANALYSIS RESULT:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        
        # Ask if user wants to analyze another image
        another = input("\n🔄 Analyze another image? (y/n): ").strip().lower()
        if another not in ['y', 'yes']:
            print("👋 Thanks for using the image analyzer!")
            break

# Example usage for direct function calls
def analyze_single_image(image_path, question="What's in this image?"):
    """Simplified function to analyze a single image."""
    
    # Encode image
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return "Failed to encode image"
    
    # Analyze with Azure OpenAI
    result = analyze_image_with_azure_openai(base64_image, question)
    return result

if __name__ == "__main__":
    main()

# Alternative: Direct usage example
"""
# Example of direct usage:
if __name__ == "__main__":
    # Set your environment variables first
    os.environ["AZUREAPI"] = "your-api-key-here"
    os.environ["AZUREENDPOINT"] = "https://your-endpoint.openai.azure.com/"
    os.environ["AZUREVERSION"] = "2024-02-01"
    
    # Analyze an image
    result = analyze_single_image("path/to/your/image.jpg", "What objects do you see in this image?")
    print(result)
"""