import { chromium } from 'playwright';
import { analyzeForm } from './form-analyzer.js';
import { fillForm } from './form-filler.js';
import { JobProfile } from './form-analyzer.js';
import * as dotenv from 'dotenv';

dotenv.config();

const testProfile: JobProfile = {
  firstName: 'John',
  lastName: 'Doe',
  gender: 'Male',
  email: 'john.doe@example.com',
  phone: '+1-555-123-4567',
  address: '123 Main St',
  city: 'San Francisco',
  state: 'California',
  zipCode: '94105',
  country: 'United States',
  currentCompany: 'Tech Corp',
  currentJobTitle: 'Senior Software Engineer',
  yearsOfExperience: 5,
  linkedinUrl: 'https://linkedin.com/in/johndoe',
  githubUrl: 'https://github.com/johndoe',
  portfolioUrl: 'https://johndoe.dev',
  highestDegree: 'Bachelor of Science',
  university: 'Stanford University',
  graduationYear: 2018,
  fieldOfStudy: 'Computer Science',
  gpa: '3.8',
  expectedSalary: '$150,000',
  workAuthorization: 'Yes',
  requiresSponsorship: false,
  willingToRelocate: true,
  preferredWorkLocation: 'Remote',
  availableStartDate: '2 weeks',
  technicalSkills: 'JavaScript, TypeScript, React, Node.js, Python',
  resumeUrl: 'https://msnlabs.com/img/resume-sample.pdf',
  coverLetterUrl: 'https://academicsuccess.ucf.edu/explearning/wp-content/uploads/sites/12/2021/09/Cover-Letter-Samples.pdf',
  whyThisCompany: 'I am passionate about your mission and would love to contribute to your innovative projects.',
  careerGoals: 'To become a technical leader in cutting-edge software development.',
};

async function test() {
  console.log('🚀 Starting Top-Notch AI Form Filler Test...\n');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 100
  });
  
  const page = await browser.newPage({
    viewport: { width: 1366, height: 768 }
  });
  
  // Navigate to the job application form
  // const testUrl = 'https://job-boards.greenhouse.io/fixify/jobs/4987787008';
  // const testUrl = 'https://job-boards.greenhouse.io/renttherunway/jobs/7395001';
  const testUrl = 'https://job-boards.greenhouse.io/twilio/jobs/7394811';
  console.log(`📍 Navigating to: ${testUrl}\n`);
  
  await page.goto(testUrl, { waitUntil: 'networkidle' });
  
  // Step 1: Analyze form with Regex-based mapping
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🔍 Step 1: Analyzing form with regex patterns...\n');
  const startAnalysis = Date.now();
  const fields = await analyzeForm(page, testProfile);
  const analysisTime = Date.now() - startAnalysis;
  
  console.log(`\n✅ Analysis complete in ${analysisTime}ms`);
  console.log(`📊 Found ${fields.length} fields total`);
  console.log(`   - ${fields.filter(f => f.required).length} required fields`);
  console.log(`   - ${fields.filter(f => f.inferredPurpose && f.inferredPurpose !== 'custom').length} mapped fields`);
  console.log(`   - ${fields.filter(f => f.isAutocomplete).length} autocomplete fields\n`);
  
  // Step 2: Fill form with human-like interactions
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('✍️  Step 2: Filling form with human-like interactions...\n');
  const startFilling = Date.now();
  await fillForm(page, fields, testProfile);
  const fillingTime = Date.now() - startFilling;
  
  console.log(`\n✅ Filling complete in ${fillingTime}ms`);
  console.log(`⏱️  Total time: ${analysisTime + fillingTime}ms\n`);
  
  // Wait for manual review
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('⏸️  Form filled successfully!');
  console.log('👀 Review the form for 2 minutes before closing...');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  // await page.waitForTimeout(120000);
  
  await browser.close();
  console.log('\n✅ Test complete! Browser closed.');
}

test().catch(error => {
  console.error('\n❌ Test failed:', error);
  process.exit(1);
});