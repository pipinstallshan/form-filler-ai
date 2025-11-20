import re
from typing import Dict, List, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup
from page_processor import expand_all_dropdowns, dedupe_html, save_all_dropdowns_in_one_html

@dataclass
class JobProfile:
    firstName: str
    lastName: str
    email: str
    phone: str
    address: str = None
    city: str = None
    state: str = None
    zipCode: str = None
    country: str = None
    currentCompany: str = None
    currentJobTitle: str = None
    yearsOfExperience: int = None
    linkedinUrl: str = None
    githubUrl: str = None
    portfolioUrl: str = None
    highestDegree: str = None
    university: str = None
    graduationYear: int = None
    fieldOfStudy: str = None
    gpa: str = None
    expectedSalary: str = None
    workAuthorization: str = None
    requiresSponsorship: bool = None
    willingToRelocate: bool = None
    availableStartDate: str = None
    technicalSkills: str = None
    resumeUrl: str = None
    coverLetterUrl: str = None
    whyThisCompany: str = None
    gender: str = None
    veteranStatus: str = None
    disabilityStatus: str = None
    race: str = None

def extract_clean_html(driver) -> str:
    print('📄 Extracting page HTML with dropdown expansion...')
    html_snapshots, dropdown_names = expand_all_dropdowns(driver)
    print(f'   📊 Collected {len(html_snapshots)} HTML snapshot(s) ({len(dropdown_names)} dropdown(s) expanded)')
    merged_soup = save_all_dropdowns_in_one_html(html_snapshots, dropdown_names)
    merged_dedupe_soup = dedupe_html(merged_soup)
    clean_html = str(merged_dedupe_soup)
    print(f'✅ Extracted {len(clean_html)} characters of HTML')
    return clean_html

def get_profile_as_dict(profile: JobProfile) -> Dict[str, Any]:
    return {
        'firstName': profile.firstName,
        'lastName': profile.lastName,
        'email': profile.email,
        'phone': profile.phone,
        'address': profile.address,
        'city': profile.city,
        'state': profile.state,
        'zipCode': profile.zipCode,
        'country': profile.country,
        'currentCompany': profile.currentCompany,
        'currentJobTitle': profile.currentJobTitle,
        'yearsOfExperience': profile.yearsOfExperience,
        'linkedinUrl': profile.linkedinUrl,
        'githubUrl': profile.githubUrl,
        'portfolioUrl': profile.portfolioUrl,
        'highestDegree': profile.highestDegree,
        'university': profile.university,
        'graduationYear': profile.graduationYear,
        'fieldOfStudy': profile.fieldOfStudy,
        'gpa': profile.gpa,
        'expectedSalary': profile.expectedSalary,
        'workAuthorization': profile.workAuthorization,
        'requiresSponsorship': profile.requiresSponsorship,
        'willingToRelocate': profile.willingToRelocate,
        'availableStartDate': profile.availableStartDate,
        'technicalSkills': profile.technicalSkills,
        'resumeUrl': profile.resumeUrl,
        'coverLetterUrl': profile.coverLetterUrl,
        'whyThisCompany': profile.whyThisCompany,
        'gender': profile.gender,
        'veteranStatus': profile.veteranStatus,
        'disabilityStatus': profile.disabilityStatus,
        'race': profile.race
    }
