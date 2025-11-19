"""
AI Form Filler - Test Script
Fully AI-driven form filling
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from form_analyzer import JobProfile, extract_clean_html, get_profile_as_dict
from ai_service import identify_form_fields, map_fields_to_profile, fill_remaining_fields
from form_filler import fill_form
from dotenv import load_dotenv

load_dotenv()

# Test profile data
test_profile = JobProfile(
    firstName='John',
    lastName='Doe',
    gender='Male',
    email='john.doe@example.com',
    phone='+1-555-123-4567',
    address='123 Main St',
    city='San Francisco',
    state='California',
    zipCode='94105',
    country='United States',
    currentCompany='Tech Corp',
    currentJobTitle='Senior Software Engineer',
    yearsOfExperience=5,
    linkedinUrl='https://linkedin.com/in/johndoe',
    githubUrl='https://github.com/johndoe',
    portfolioUrl='https://johndoe.dev',
    highestDegree='Bachelor of Science',
    university='Stanford University',
    graduationYear=2018,
    fieldOfStudy='Computer Science',
    gpa='3.8',
    expectedSalary='$150,000',
    workAuthorization='Yes',
    requiresSponsorship=False,
    willingToRelocate=True,
    availableStartDate='2 weeks',
    technicalSkills='JavaScript, TypeScript, React, Node.js, Python',
    resumeUrl='https://msnlabs.com/img/resume-sample.pdf',
    coverLetterUrl='https://academicsuccess.ucf.edu/explearning/wp-content/uploads/sites/12/2021/09/Cover-Letter-Samples.pdf',
    whyThisCompany='I am passionate about your mission and would love to contribute to your innovative projects.',
)


def test():
    """Main test function - AI-driven form filling"""
    print('🚀 AI Form Filler - Starting...\n')
    print('=' * 60 + '\n')
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1366, 768)
    
    try:
        # Navigate to form
        test_url = 'https://job-boards.greenhouse.io/twilio/jobs/7394811'
        print(f'📍 Navigating to: {test_url}\n')
        driver.get(test_url)
        
        # Wait for page to load
        print('⏳ Waiting for page to load...')
        time.sleep(3)
        print('✅ Page loaded\n')
        
        # STEP 1: Extract clean HTML
        print('=' * 60)
        html = extract_clean_html(driver)
        print()
        
        # STEP 2: Use AI to identify form fields
        print('=' * 60)
        profile_dict = get_profile_as_dict(test_profile)
        fields = identify_form_fields(html, profile_dict)
        
        if not fields:
            print('❌ No fields identified by AI!')
            return
        print()
        
        # STEP 3: Map profile data to fields
        print('=' * 60)
        field_values = map_fields_to_profile(fields, profile_dict)
        print()
        
        # STEP 4: Fill the form with mapped values
        print('=' * 60)
        filled_count = fill_form(driver, fields, field_values)
        print()
        
        # STEP 5: Check what's left and fill with AI
        print('=' * 60)
        print('🤖 Checking for remaining empty fields...')
        time.sleep(2)
        
        # Get updated HTML
        html_after = extract_clean_html(driver)
        filled_labels = list(field_values.keys())
        remaining_values = fill_remaining_fields(html_after, filled_labels, profile_dict)
        
        if remaining_values:
            print(f'\n📝 Filling {len(remaining_values)} remaining fields...\n')
            fill_form(driver, fields, remaining_values)
        else:
            print('✅ No remaining fields to fill')
        print()
        
        # Done
        print('=' * 60)
        print('🎉 Form filling complete!')
        print('👀 Review the form before submitting...')
        print('=' * 60)
        
        input('\nPress Enter to close browser...')
        
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print('\n✅ Browser closed.')


if __name__ == '__main__':
    try:
        test()
    except KeyboardInterrupt:
        print('\n\n❌ Interrupted by user')
    except Exception as error:
        print(f'\n❌ Test failed: {error}')
        import traceback
        traceback.print_exc()
