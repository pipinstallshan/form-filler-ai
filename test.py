import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from form_analyzer import JobProfile, extract_clean_html, get_profile_as_dict
from ai_service import identify_form_fields, map_fields_to_profile, fill_remaining_fields
from form_filler import fill_form
from dotenv import load_dotenv

load_dotenv()

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
    print('🚀 AI Form Filler - Starting...\n')
    print('=' * 60 + '\n')
    
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1366, 768)
    
    try:
        test_url = 'https://job-boards.greenhouse.io/fixify/jobs/4985488008'
        test_url = 'https://job-boards.greenhouse.io/renttherunway/jobs/7395001'
        test_url = 'https://job-boards.greenhouse.io/twilio/jobs/7394811'
        print(f'📍 Navigating to: {test_url}\n')
        driver.get(test_url)
        
        print('⏳ Waiting for page to load...')
        print('✅ Page loaded\n')
        
        print('=' * 60)
        profile_dict = get_profile_as_dict(test_profile)
        html = extract_clean_html(driver)
        
        print('=' * 60)
        fields = identify_form_fields(html, profile_dict, use_cache=False)
        print()
        
        print('=' * 60)
        field_values = map_fields_to_profile(fields, profile_dict)
        print()
        
        print('=' * 60)
        filled_count = fill_form(driver, fields, field_values)
        print()
        
        print('=' * 60)
        print('🤖 Checking for remaining empty fields...')
        time.sleep(2)
        
        html_after = extract_clean_html(driver)
        filled_labels = list(field_values.keys())
        remaining_values = fill_remaining_fields(html_after, filled_labels, profile_dict)
        
        if remaining_values:
            print(f'\n📝 Filling {len(remaining_values)} remaining fields...\n')
            fill_form(driver, fields, remaining_values)
        else:
            print('✅ No remaining fields to fill')
        print()
        
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
