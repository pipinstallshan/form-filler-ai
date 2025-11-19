"""
AI-First Form Analyzer
Extracts HTML and uses AI to identify form fields
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class JobProfile:
    """Job application profile data"""
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
    """Extract body HTML and remove unnecessary tags"""
    print('📄 Extracting page HTML...')
    
    # Get the full page HTML
    html = driver.page_source
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unnecessary tags
    for tag in soup(['script', 'style', 'noscript', 'svg', 'path', 'iframe', 'img']):
        tag.decompose()
    
    # Get body only
    body = soup.find('body')
    if not body:
        body = soup
    
    # Clean up whitespace
    clean_html = str(body)
    clean_html = re.sub(r'\s+', ' ', clean_html)
    clean_html = re.sub(r'>\s+<', '><', clean_html)
    
    print(f'✅ Extracted {len(clean_html)} characters of HTML')
    return clean_html


def get_profile_as_dict(profile: JobProfile) -> Dict[str, Any]:
    """Convert profile to dictionary for AI"""
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
