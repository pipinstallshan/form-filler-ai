import { FormField, JobProfile, InferredPurpose } from './form-analyzer.js';
import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';
import * as dotenv from 'dotenv';

dotenv.config();

/**
 * Use AI to intelligently answer a question based on profile data and question context
 */
async function getIntelligentAnswer(field: FormField, profile: JobProfile, options?: string[]): Promise<string | null> {
  const apiKey = process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    console.log(`    ⚠️  No GOOGLE_API_KEY found, skipping AI-powered answer`);
    return null;
  }

  try {
    // Build context from profile data
    const profileContext = {
      name: `${profile.firstName} ${profile.lastName}`,
      firstName: profile.firstName,
      lastName: profile.lastName,
      email: profile.email,
      phone: profile.phone,
      location: [profile.city, profile.state, profile.country].filter(Boolean).join(', '),
      currentJob: profile.currentJobTitle,
      currentCompany: profile.currentCompany,
      experience: profile.yearsOfExperience,
      skills: profile.technicalSkills,
      education: profile.highestDegree ? `${profile.highestDegree} in ${profile.fieldOfStudy || 'N/A'}` : null,
      university: profile.university,
      linkedin: profile.linkedinUrl,
      github: profile.githubUrl,
      portfolio: profile.portfolioUrl,
      workAuth: profile.workAuthorization,
      sponsorship: profile.requiresSponsorship,
      relocate: profile.willingToRelocate,
      salary: profile.expectedSalary,
      startDate: profile.availableStartDate,
      whyCompany: profile.whyThisCompany,
      careerGoals: profile.careerGoals
    };

    // Build prompt
    const questionText = field.label || field.placeholder || field.name || '';
    const fieldType = field.type;
    const isRequired = field.required;
    
    let prompt = `You are helping fill out a job application form. Based on the candidate's profile data, provide an appropriate answer to this question.

QUESTION: "${questionText}"
FIELD TYPE: ${fieldType}
REQUIRED: ${isRequired ? 'Yes' : 'No'}

CANDIDATE PROFILE:
${JSON.stringify(profileContext, null, 2)}

`;

    if (options && options.length > 0) {
      prompt += `AVAILABLE OPTIONS (select one):\n${options.map((opt, i) => `${i + 1}. ${opt}`).join('\n')}\n\n`;
      prompt += `INSTRUCTIONS:
- If this is a dropdown/select field, choose the BEST MATCHING option from the list above
- Return ONLY the option text exactly as it appears in the list
- If no good match exists, choose the closest option
- For Yes/No questions, choose "Yes" for positive attributes (work authorization, willing to relocate) unless profile says otherwise
- For eligibility questions, default to "Yes" or "Authorized"
`;
    } else {
      prompt += `INSTRUCTIONS:
- Provide a concise, professional answer (1-3 sentences max for text fields)
- Use first person ("I", "My", "Me")
- Be specific and authentic based on the profile data
- If asking about location/address, provide the location from profile
- If asking about experience, use the years of experience
- If asking "why this company", use the whyThisCompany field or generate a professional response
- If asking about availability, use availableStartDate or say "Immediately available" or "2 weeks notice"
- For Yes/No questions, answer "Yes" for positive attributes unless profile indicates otherwise
- NEVER use "N/A", "Not provided", or leave blank - always provide a thoughtful answer
- If data is missing, make a reasonable inference based on the profile context
`;
    }

    prompt += `\nReturn ONLY the answer text, nothing else.`;

    // Try multiple Gemini models in order of preference
    const models = [
      'gemini-2.0-flash-exp',
      'gemini-1.5-flash',
      'gemini-1.5-pro'
    ];
    
    for (const model of models) {
      try {
        const response = await axios.post(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
          {
            contents: [{
              parts: [{
                text: prompt
              }]
            }],
            generationConfig: {
              temperature: 0.7,
              topK: 40,
              topP: 0.95,
              maxOutputTokens: 200,
            }
          },
          {
            headers: {
              'Content-Type': 'application/json'
            },
            timeout: 10000
          }
        );

        const answer = response.data?.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
        
        if (answer) {
          console.log(`    🤖 AI-generated answer (${model}): "${answer}"`);
          return answer;
        }
      } catch (modelError: any) {
        // Try next model if this one fails
        if (model !== models[models.length - 1]) {
          continue;
        }
        throw modelError;
      }
    }

    return null;
  } catch (error: any) {
    console.log(`    ⚠️  AI answer generation failed: ${error.message}`);
    return null;
  }
}

/**
 * Map profile data to field based on inferred purpose
 */
function mapProfileToField(purpose: InferredPurpose | undefined, profile: JobProfile): any {
  if (!purpose || purpose === 'custom') return null;
  
  const directMap: Record<string, any> = {
    // Personal Information
    firstName: profile.firstName,
    lastName: profile.lastName,
    fullName: `${profile.firstName} ${profile.lastName}`.trim(),
    email: profile.email,
    phone: profile.phone,
    address: profile.address,
    city: profile.city,
    state: profile.state,
    zipCode: profile.zipCode,
    country: profile.country,
    
    // Professional Information
    currentCompany: profile.currentCompany,
    currentJobTitle: profile.currentJobTitle,
    yearsOfExperience: profile.yearsOfExperience,
    
    // URLs
    linkedinUrl: profile.linkedinUrl,
    githubUrl: profile.githubUrl,
    portfolioUrl: profile.portfolioUrl,
    websiteUrl: profile.websiteUrl || profile.portfolioUrl,
    
    // Education
    highestDegree: profile.highestDegree,
    university: profile.university,
    graduationYear: profile.graduationYear,
    fieldOfStudy: profile.fieldOfStudy,
    gpa: profile.gpa,
    
    // Work Preferences
    expectedSalary: profile.expectedSalary,
    currentSalary: profile.currentSalary,
    noticePeriod: profile.noticePeriod,
    availableStartDate: profile.availableStartDate,
    workAuthorization: profile.workAuthorization,
    requiresSponsorship: profile.requiresSponsorship ? 'Yes' : 'No',
    willingToRelocate: profile.willingToRelocate ? 'Yes' : 'No',
    preferredWorkLocation: profile.preferredWorkLocation,
    
    // Skills & Certifications
    technicalSkills: profile.technicalSkills,
    certifications: profile.certifications,
    
    // Documents (URLs for download)
    resume: profile.resumeUrl,
    coverLetter: profile.coverLetterUrl,
    
    // Additional Information
    whyThisCompany: profile.whyThisCompany,
    careerGoals: profile.careerGoals,
    referralSource: profile.referralSource,
    hearAboutUs: profile.referralSource || 'Online Job Board',
    
    // EEO Information (provide defaults to skip these fields gracefully)
    veteranStatus: profile.veteranStatus || 'I don\'t wish to answer',
    disabilityStatus: profile.disabilityStatus || 'I don\'t wish to answer',
    gender: profile.gender || 'Prefer not to say',
    race: profile.race || 'Prefer not to say',
  };
  
  return directMap[purpose];
}

/**
 * Download file from URL to temp location
 */
async function downloadFile(url: string, filename: string): Promise<string> {
  const tempDir = path.join(process.cwd(), 'temp');
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  
  // Ensure filename has proper extension
  if (!filename.includes('.')) {
    // Try to get extension from URL or default to .pdf
    const urlExt = url.split('.').pop()?.split('?')[0] || 'pdf';
    filename = `${filename}.${urlExt}`;
  }
  
  const tempPath = path.join(tempDir, filename);
  
  console.log(`    📥 Downloading file from: ${url}`);
  console.log(`    💾 Saving to: ${tempPath}`);
  
  try {
    const response = await axios.get(url, { 
      responseType: 'stream',
      timeout: 30000, // 30 second timeout
      maxRedirects: 5
    });
    
    const writer = fs.createWriteStream(tempPath);
    
    response.data.pipe(writer);
    
    return new Promise((resolve, reject) => {
      writer.on('finish', () => {
        // Verify file was actually written
        if (fs.existsSync(tempPath)) {
          const stats = fs.statSync(tempPath);
          if (stats.size > 0) {
            console.log(`    ✅ File downloaded successfully (${stats.size} bytes)`);
            resolve(tempPath);
          } else {
            reject(new Error('Downloaded file is empty'));
          }
        } else {
          reject(new Error('File was not created'));
        }
      });
      writer.on('error', (err) => {
        // Clean up partial file
        if (fs.existsSync(tempPath)) {
          fs.unlinkSync(tempPath);
        }
        reject(err);
      });
      response.data.on('error', (err: any) => {
        writer.destroy();
        if (fs.existsSync(tempPath)) {
          fs.unlinkSync(tempPath);
        }
        reject(err);
      });
    });
  } catch (error: any) {
    // Clean up on error
    if (fs.existsSync(tempPath)) {
      fs.unlinkSync(tempPath);
    }
    throw new Error(`Failed to download file: ${error.message}`);
  }
}

/**
 * Clean up temp files
 */
function cleanup(filePath: string) {
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }
}

/**
 * Handle autocomplete dropdown field - USE THIS FOR ALL DROPDOWNS (both autocomplete and regular select)
 */
async function fillAutocompleteField(page: any, field: FormField, value: any): Promise<void> {
  const { selector, type } = field;
  
  // Check if it's a native <select> element first - try quick native method
  const isNativeSelect = await page.evaluate((sel: string) => {
    const el = document.querySelector(sel);
    return el?.tagName === 'SELECT';
  }, selector).catch(() => false);
  
  // For native <select>, try Playwright's selectOption first (faster and more reliable)
  if (isNativeSelect && type === 'select') {
    try {
      console.log(`    🔍 Handling native <select> dropdown: ${value}`);
      
      // Try multiple selection strategies
      try {
        await page.selectOption(selector, { label: String(value) });
        console.log(`    ✓ Selected by label: ${value}`);
        
        // Verify it worked
        await page.waitForTimeout(300);
        const verified = await page.evaluate((sel: string) => {
          const select = document.querySelector(sel) as HTMLSelectElement;
          const selectedText = select?.options[select.selectedIndex]?.text || '';
          return selectedText && !selectedText.toLowerCase().includes('select');
        }, selector);
        
        if (verified) {
          await page.locator(selector).press('Tab');
          await page.waitForTimeout(200);
          return; // Success!
        }
      } catch (e1) {
        // Try value match
        try {
          await page.selectOption(selector, { value: String(value) });
          console.log(`    ✓ Selected by value: ${value}`);
          await page.locator(selector).press('Tab');
          await page.waitForTimeout(200);
          return; // Success!
        } catch (e2) {
          // Continue to autocomplete method below
        }
      }
    } catch (e) {
      // Fall through to autocomplete method
    }
  }
  
  // Use robust autocomplete method for all dropdowns (works for both native and custom)
  console.log(`    🔍 Handling dropdown (autocomplete method): ${value}`);
  console.log(`    📍 Selector: ${selector}, Field name: ${field.name}, Label: ${field.label}, Type: ${type}`);
  
  // First, clear any existing value (only for input-like fields, not native select)
  if (!isNativeSelect) {
    try {
      await page.locator(selector).fill('');
      await page.waitForTimeout(200);
    } catch (e) {
      // If fill doesn't work, try clear
      try {
        await page.locator(selector).clear();
        await page.waitForTimeout(200);
      } catch (e2) {
        // Ignore - might be a native select
      }
    }
  }
  
  // Try multiple click strategies to open dropdown
  let dropdownOpened = false;
  const clickStrategies = [
    async () => {
      await page.locator(selector).click();
      return true;
    },
    async () => {
      await page.click(selector);
      return true;
    },
    async () => {
      const clicked = await page.evaluate((sel: string) => {
        const el = document.querySelector(sel) as HTMLElement;
        if (el) {
          el.focus();
          el.click();
          return true;
        }
        return false;
      }, selector);
      return clicked;
    }
  ];
  
  for (const clickStrategy of clickStrategies) {
    try {
      await clickStrategy();
      await page.waitForTimeout(500);
      
      // Check if dropdown opened by looking for options
      const hasOptions = await page.evaluate(() => {
        return document.querySelectorAll('[role="option"], [role="listbox"], .dropdown-menu, .select-options').length > 0;
      });
      
      if (hasOptions) {
        dropdownOpened = true;
        console.log(`    ✓ Dropdown opened`);
        break;
      }
      
      await page.waitForTimeout(500); // Wait a bit more
    } catch (e) {
      continue;
    }
  }
  
  if (!dropdownOpened) {
    console.log(`    ⚠️  Could not open dropdown with clicks, trying keyboard`);
    try {
      await page.locator(selector).focus();
      await page.waitForTimeout(200);
      await page.locator(selector).press('Space');
      await page.waitForTimeout(800);
      
      // Check again
      const hasOptions = await page.evaluate(() => {
        return document.querySelectorAll('[role="option"], [role="listbox"], .dropdown-menu, .select-options').length > 0;
      });
      dropdownOpened = hasOptions;
    } catch (e) {
      console.log(`    ⚠️  Keyboard open also failed: ${e}`);
    }
  }
  
  // For native select, try direct option selection via evaluate first
  if (isNativeSelect) {
    const directSelect = await page.evaluate(({ sel, val }: { sel: string; val: string }) => {
      const select = document.querySelector(sel) as HTMLSelectElement;
      if (!select) return false;
      
      const options = Array.from(select.options);
      const match = options.find(opt => {
        const optText = opt.text.toLowerCase().trim();
        const optValue = opt.value.toLowerCase().trim();
        const valLower = val.toLowerCase().trim();
        return optText === valLower || 
               optValue === valLower ||
               optText.includes(valLower) ||
               valLower.includes(optText) ||
               optText.startsWith(valLower.substring(0, Math.min(5, valLower.length)));
      });
      
      if (match) {
        select.value = match.value;
        select.selectedIndex = match.index;
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
        select.dispatchEvent(new Event('blur', { bubbles: true }));
        return true;
      }
      return false;
    }, { sel: selector, val: String(value) });
    
    if (directSelect) {
      console.log(`    ✓ Selected native select via evaluate: ${value}`);
      await page.waitForTimeout(500);
      await page.locator(selector).press('Tab');
      await page.waitForTimeout(200);
      return; // Success!
    }
  }
  
  // Type to filter options - clear first, then type (for autocomplete/custom dropdowns)
  const searchTerm = String(value).substring(0, Math.min(15, String(value).length));
  console.log(`    ⌨️  Typing search term: "${searchTerm}"`);
  
  // Clear the field again before typing (only for input-like fields)
  if (!isNativeSelect) {
    try {
      await page.locator(selector).fill('');
      await page.waitForTimeout(100);
    } catch (e) {
      // Ignore
    }
    
    // Type character by character to trigger autocomplete
    for (let i = 0; i < searchTerm.length; i++) {
      await page.locator(selector).type(searchTerm[i], { delay: 100 });
      await page.waitForTimeout(100);
    }
    
    await page.waitForTimeout(1500); // Wait for filtered results to appear
  } else {
    // For native select, just wait a bit after opening
    await page.waitForTimeout(500);
  }
  
  // Check if options are visible now
  const optionsVisible = await page.evaluate(() => {
    const options = Array.from(document.querySelectorAll('[role="option"], [role="listbox"] li, .dropdown-option'));
    return options.filter((opt: any) => opt.offsetParent !== null).length;
  });
  console.log(`    📊 Found ${optionsVisible} visible options after typing`);
  
  // Try multiple strategies to find and click the option
  let optionClicked = false;
  const valueStr = String(value);
  
  // Strategy 1: Look for visible options with role="option" - try exact match first
  console.log(`    🔍 Strategy 1: Looking for exact/partial match in role="option"`);
  optionClicked = await page.evaluate(({ val, sel }: { val: string; sel: string }) => {
    const allOptions = Array.from(document.querySelectorAll('[role="option"]'));
    const visibleOptions = allOptions.filter((opt: any) => opt.offsetParent !== null);
    
    // Try exact match first
    let match = visibleOptions.find((opt: any) => {
      const text = opt.textContent?.trim() || '';
      return text.toLowerCase() === val.toLowerCase();
    }) as HTMLElement;
    
    // Try partial match
    if (!match) {
      match = visibleOptions.find((opt: any) => {
        const text = opt.textContent?.trim() || '';
        const normalizedText = text.toLowerCase();
        const normalizedVal = val.toLowerCase();
        return normalizedText.includes(normalizedVal) || 
               normalizedVal.includes(normalizedText) ||
               normalizedText.startsWith(normalizedVal.substring(0, Math.min(5, normalizedVal.length)));
      }) as HTMLElement;
    }
    
    if (match) {
      match.scrollIntoView({ behavior: 'auto', block: 'center' });
      // Try multiple click methods and trigger events to ensure value sticks
      try {
        match.click();
        
        // Also trigger mouse events to ensure it registers
        match.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
        match.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
        match.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        
        // Find the associated input and update its value if it's an input field
        const input = document.querySelector(sel) as HTMLInputElement;
        if (input && input.tagName === 'INPUT') {
          const text = match.textContent?.trim() || '';
          input.value = text;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
          input.dispatchEvent(new Event('blur', { bubbles: true }));
        }
      } catch (e) {
        // Try mouse event
        const event = new MouseEvent('click', { bubbles: true, cancelable: true });
        match.dispatchEvent(event);
      }
      return true;
    }
    return false;
  }, { val: valueStr, sel: selector });
  
  // Strategy 2: Look in listbox or dropdown containers
  if (!optionClicked) {
    console.log(`    🔍 Strategy 2: Looking in listbox/dropdown containers`);
    await page.waitForTimeout(500);
    optionClicked = await page.evaluate(({ val }: { val: string }) => {
      const containers = [
        '[role="listbox"]',
        '.dropdown-menu',
        '.select-options',
        '.autocomplete-options',
        '[class*="dropdown"]',
        '[class*="select"]'
      ];
      
      for (const containerSel of containers) {
        const container = document.querySelector(containerSel);
        if (container) {
          const options = Array.from(container.querySelectorAll('li, div, span, [role="option"]'));
          const visibleOptions = options.filter((opt: any) => opt.offsetParent !== null);
          
          const match = visibleOptions.find((opt: any) => {
            const text = opt.textContent?.trim() || '';
            const normalizedText = text.toLowerCase();
            const normalizedVal = val.toLowerCase();
            return normalizedText === normalizedVal || 
                   normalizedText.includes(normalizedVal) || 
                   normalizedVal.includes(normalizedText);
          }) as HTMLElement;
          
          if (match) {
            match.scrollIntoView({ behavior: 'auto', block: 'center' });
            
            // Click and trigger events
            match.click();
            match.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
            match.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
            match.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            
            return true;
          }
        }
      }
      return false;
    }, { val: valueStr });
  }
  
  // Strategy 3: Try clicking by text content using Playwright
  if (!optionClicked) {
    console.log(`    🔍 Strategy 3: Using Playwright text-based selection`);
    try {
      // Try to find and click by text
      const optionLocator = page.locator(`[role="option"]:has-text("${valueStr}")`).first();
      const count = await optionLocator.count();
      if (count > 0) {
        await optionLocator.scrollIntoViewIfNeeded();
        await optionLocator.click();
        optionClicked = true;
        console.log(`    ✓ Clicked option by text`);
      }
    } catch (e) {
      // Try partial text match
      try {
        const partialMatch = valueStr.substring(0, Math.min(10, valueStr.length));
        const optionLocator = page.locator(`[role="option"]`).filter({ hasText: partialMatch }).first();
        const count = await optionLocator.count();
        if (count > 0) {
          await optionLocator.scrollIntoViewIfNeeded();
          await optionLocator.click();
          optionClicked = true;
          console.log(`    ✓ Clicked option by partial text`);
        }
      } catch (e2) {
        // Continue to next strategy
      }
    }
  }
  
  // Strategy 4: Keyboard navigation
  if (!optionClicked) {
    console.log(`    ⚡ Strategy 4: Using keyboard navigation fallback`);
    try {
      await page.locator(selector).press('ArrowDown');
      await page.waitForTimeout(300);
      await page.locator(selector).press('Enter');
      await page.waitForTimeout(500);
      optionClicked = true; // Assume it worked
    } catch (e) {
      console.log(`    ⚠️  Keyboard navigation failed: ${e}`);
    }
  }
  
  if (optionClicked) {
    console.log(`    ✓ Selected autocomplete option: ${value}`);
    await page.waitForTimeout(800); // Wait longer for UI to update
    
    // Verify the selection stuck - check multiple places where the value might be stored
    const verification = await page.evaluate(({ sel, val }: { sel: string; val: string }) => {
      const el = document.querySelector(sel) as HTMLInputElement | HTMLSelectElement;
      if (!el) return { success: false, reason: 'Element not found' };
      
      // Check input value
      const inputValue = (el as HTMLInputElement)?.value || '';
      
      // Check for hidden input that might store the actual value
      const hiddenInput = el.closest('div, span, label')?.querySelector('input[type="hidden"]') as HTMLInputElement;
      const hiddenValue = hiddenInput?.value || '';
      
      // Check select element selected option
      let selectValue = '';
      if (el.tagName === 'SELECT') {
        const select = el as HTMLSelectElement;
        selectValue = select.options[select.selectedIndex]?.text || '';
      }
      
      // Check displayed text in the container (for custom dropdowns)
      const container = el.closest('div, span, label, [class*="dropdown"], [class*="select"]');
      const containerText = container?.textContent?.trim() || '';
      const containerInnerText = (container as HTMLElement)?.innerText?.trim() || '';
      
      // Check for aria-label or aria-labelledby
      const ariaLabel = el.getAttribute('aria-label') || '';
      
      // Check if the value appears anywhere in the visible text
      const valLower = val.toLowerCase();
      const allText = [inputValue, hiddenValue, selectValue, containerText, containerInnerText, ariaLabel]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      
      const valueFound = allText.includes(valLower) || 
                        valLower.includes(allText.substring(0, Math.min(20, allText.length)));
      
      return {
        success: valueFound,
        inputValue,
        hiddenValue,
        selectValue,
        containerText: containerText.substring(0, 100),
        tagName: el.tagName,
        type: (el as HTMLInputElement)?.type,
        valueFound
      };
    }, { sel: selector, val: String(value) });
    
    console.log(`    📋 Verification:`, verification);
    
    if (verification.success || verification.valueFound) {
      console.log(`    ✅ Selection verified and persisted!`);
    } else {
      // Try one more time to ensure the value is set
      console.log(`    ⚠️  Verification unclear, re-checking...`);
      await page.waitForTimeout(500);
      
      // Double-check by reading the field again
      const finalCheck = await page.evaluate((sel: string) => {
        const el = document.querySelector(sel);
        if (!el) return false;
        
        // Check if field has any value or text
        const hasValue = (el as HTMLInputElement)?.value || 
                        (el as HTMLSelectElement)?.options[(el as HTMLSelectElement).selectedIndex]?.text ||
                        el.textContent?.trim();
        
        return !!hasValue && !hasValue.toLowerCase().includes('select') && 
               !hasValue.toLowerCase().includes('choose');
      }, selector);
      
      if (finalCheck) {
        console.log(`    ✅ Selection confirmed on re-check!`);
      } else {
        console.log(`    ⚠️  Selection may not have registered - but continuing anyway`);
      }
    }
  } else {
    console.log(`    ⚠️  Could not select autocomplete option: ${value}`);
  }
  
  // Press Tab to move to next field
  await page.locator(selector).press('Tab');
  await page.waitForTimeout(200);
}

/**
 * Fill a single field with human-like interaction
 */
async function fillField(page: any, field: FormField, value: any): Promise<void> {
  const { selector, type, isAutocomplete } = field;
  
  console.log(`  Filling: ${field.label} (${type}) with: ${JSON.stringify(value)}`);
  if (isAutocomplete) {
    console.log(`    ⚠️  Autocomplete field - using special handling`);
  }
  
  // Explicitly check if this is a phone field
  const isPhoneField = type === 'tel' || /phone|telephone|mobile/i.test(field.label || field.name || '');
  if (isPhoneField) {
    console.log(`    📞 Phone field detected - using tel handling`);
  }
  
  try {
    // Wait for element to be available
    await page.waitForSelector(selector, { timeout: 5000 });
    
    // File inputs are often hidden, skip hover for them
    if (type !== 'file') {
      // Human-like interaction: hover before action
      await page.hover(selector);
      await page.waitForTimeout(200);
    }
    
    // Handle ALL dropdowns (both autocomplete and regular select) using the robust autocomplete method
    // Also handle text fields that are detected as autocomplete (like "Are you located in Ireland?")
    // BUT exclude phone/tel fields - they should be handled as regular text inputs
    if (!isPhoneField && (isAutocomplete || type === 'select' || 
        (type === 'text' && (field.isAutocomplete || /yes|no|ireland|county|sponsorship|visa|authorization/i.test(field.label || ''))))) {
      console.log(`    🔽 Using dropdown/autocomplete handler`);
      await fillAutocompleteField(page, field, value);
      return; // Exit early after handling dropdown
    }
    
    switch (type) {
      case 'text':
        // Regular text field
        console.log(`    ⌨️  Typing text value`);
        await page.click(selector);
        await page.waitForTimeout(100);
        await page.fill(selector, '');
        await page.waitForTimeout(50);
        await page.type(selector, String(value), { delay: 50 });
        break;
      
      case 'email':
      case 'url':
      case 'number':
        console.log(`    ⌨️  Typing ${type} value`);
        await page.click(selector);
        await page.waitForTimeout(100);
        await page.fill(selector, '');
        await page.waitForTimeout(50);
        await page.type(selector, String(value), { delay: 50 });
        break;
      
      case 'tel':
        // Remove country code prefix like +1, +92, etc
        console.log(`    📞 Processing phone number`);
        let phoneValue = String(value);
        const originalValue = phoneValue;
        phoneValue = phoneValue.replace(/^\+\d{1,3}[-\s]?/, '');
        console.log(`    📞 Phone value: "${originalValue}" -> "${phoneValue}"`);
        // Phone is just a text field - use simple fill, no delays or typing needed
        await page.fill(selector, phoneValue);
        console.log(`    ✅ Phone number filled: "${phoneValue}"`);
        break;
      
      case 'textarea':
        await page.click(selector);
        await page.waitForTimeout(100);
        await page.fill(selector, '');
        await page.waitForTimeout(50);
        await page.type(selector, String(value), { delay: 30 });
        break;
      
      case 'radio':
      case 'radio-group':
        const radioSelector = `input[name="${field.name}"][value="${value}"], ${selector}[value="${value}"]`;
        try {
          await page.hover(radioSelector);
          await page.waitForTimeout(200);
          await page.click(radioSelector);
        } catch (e) {
          const clicked = await page.evaluate(({ name, val }: { name: string; val: string }) => {
            const radios = document.querySelectorAll(`input[name="${name}"]`);
            for (const radio of radios) {
              const label = radio.closest('label')?.textContent?.trim() || '';
              if (label.toLowerCase().includes(val.toLowerCase())) {
                (radio as HTMLElement).click();
                return true;
              }
            }
            return false;
          }, { name: field.name, val: String(value) });
          if (!clicked) console.log(`    ⚠️  Could not find radio option`);
        }
        // Press Tab to move to next field
        await page.locator(radioSelector).press('Tab');
        await page.waitForTimeout(200);
        break;
      
      case 'checkbox':
        await page.hover(selector);
        await page.waitForTimeout(200);
        if (value === true || value === 'true' || value === 'Yes') {
          await page.check(selector);
        } else {
          await page.uncheck(selector);
        }
        // Press Tab to move to next field
        await page.locator(selector).press('Tab');
        await page.waitForTimeout(200);
        break;
      
      case 'checkbox-group':
        console.log(`    ☑️  Handling checkbox group: "${field.label || field.name}"`);
        
        // If required checkbox group and no value provided, automatically select first available option
        if (field.required && (!value || (Array.isArray(value) && value.length === 0))) {
          console.log(`    📋 Required checkbox group - will select first available option`);
          // Get first available option from field options or extract from page
          let firstOption = null;
          if (field.options && field.options.length > 0) {
            const firstOpt = field.options[0];
            if (typeof firstOpt === 'string') {
              firstOption = firstOpt;
            } else if (firstOpt && typeof firstOpt === 'object') {
              firstOption = (firstOpt as any).value || (firstOpt as any).text || (firstOpt as any).label;
            }
          } else {
            // Extract from page - prefer label text over value
            firstOption = await page.evaluate((name: string) => {
              const checkboxes = document.querySelectorAll(`input[name="${name}"][type="checkbox"]`) as NodeListOf<HTMLInputElement>;
              if (checkboxes.length > 0) {
                // Try to get label text first (more meaningful)
                const firstCheckbox = checkboxes[0];
                const label = document.querySelector(`label[for="${firstCheckbox.id}"]`)?.textContent?.trim();
                if (label) return label;
                // Fallback to value
                return firstCheckbox.value || 'first';
              }
              return null;
            }, field.name || '').catch(() => null);
          }
          
          if (firstOption) {
            value = [firstOption];
            console.log(`    ✅ Auto-selected: "${firstOption}"`);
          } else {
            // Last resort: just check the first checkbox by index
            try {
              await page.evaluate((name: string) => {
                const checkboxes = document.querySelectorAll(`input[name="${name}"][type="checkbox"]`) as NodeListOf<HTMLInputElement>;
                if (checkboxes.length > 0) {
                  checkboxes[0].checked = true;
                  checkboxes[0].dispatchEvent(new Event('change', { bubbles: true }));
                }
              }, field.name || '');
              console.log(`    ✅ Auto-checked first checkbox`);
            } catch (e) {
              console.log(`    ⚠️  Could not auto-select checkbox`);
            }
            break;
          }
        }
        
        if (Array.isArray(value)) {
          for (const val of value) {
            try {
              // Try exact value match first
              const checkboxSelector = `input[name="${field.name}"][value="${val}"]`;
              await page.check(checkboxSelector);
              console.log(`    ✅ Checked: "${val}"`);
            } catch (e1) {
              // Try matching by label text
              try {
                const checked = await page.evaluate(({ name, val }: { name: string; val: string }) => {
                  const checkboxes = document.querySelectorAll(`input[name="${name}"][type="checkbox"]`) as NodeListOf<HTMLInputElement>;
                  const valLower = val.toLowerCase();
                  
                  for (const checkbox of checkboxes) {
                    const label = document.querySelector(`label[for="${checkbox.id}"]`)?.textContent?.trim().toLowerCase() || '';
                    const checkboxValue = checkbox.value?.toLowerCase() || '';
                    
                    if (label.includes(valLower) || 
                        valLower.includes(label) ||
                        checkboxValue === valLower ||
                        valLower.includes(checkboxValue)) {
                      checkbox.checked = true;
                      checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                      return true;
                    }
                  }
                  return false;
                }, { name: field.name || '', val: String(val) });
                
                if (checked) {
                  console.log(`    ✅ Checked by label match: "${val}"`);
                } else {
                  console.log(`    ⚠️  Could not find checkbox: "${val}"`);
                }
              } catch (e2) {
                console.log(`    ⚠️  Could not check: "${val}"`);
              }
            }
          }
        } else if (value) {
          // Single value - try to check it
          try {
            const checkboxSelector = `input[name="${field.name}"][value="${value}"]`;
            await page.check(checkboxSelector);
            console.log(`    ✅ Checked: "${value}"`);
          } catch (e) {
            // Try label match
            await page.evaluate(({ name, val }: { name: string; val: string }) => {
              const checkboxes = document.querySelectorAll(`input[name="${name}"][type="checkbox"]`) as NodeListOf<HTMLInputElement>;
              const valLower = val.toLowerCase();
              
              for (const checkbox of checkboxes) {
                const label = document.querySelector(`label[for="${checkbox.id}"]`)?.textContent?.trim().toLowerCase() || '';
                if (label.includes(valLower) || valLower.includes(label)) {
                  checkbox.checked = true;
                  checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                  return;
                }
              }
            }, { name: field.name || '', val: String(value) });
          }
        }
        break;
      
      case 'file':
        let filePath = value;
        let tempFile = false;
        
        // Check if value is a URL (http or https)
        if (typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'))) {
          try {
            // Extract filename from URL or use default
            const urlParts = value.split('/');
            let filename = urlParts[urlParts.length - 1] || 'file.pdf';
            // Remove query parameters
            filename = filename.split('?')[0];
            // If no extension, try to detect from content-type or default to pdf
            if (!filename.includes('.')) {
              filename = filename + '.pdf';
            }
            
            filePath = await downloadFile(value, filename);
            tempFile = true;
            console.log(`    ✅ Downloaded file to: ${filePath}`);
          } catch (downloadError: any) {
            console.log(`    ❌ Failed to download file: ${downloadError.message}`);
            throw downloadError; // Re-throw to skip this field
          }
        } else if (typeof value === 'string' && fs.existsSync(value)) {
          // Local file path
          filePath = value;
          console.log(`    📁 Using local file: ${filePath}`);
        } else {
          console.log(`    ⚠️  Invalid file value: ${value}`);
          throw new Error(`Invalid file value: ${value}`);
        }
        
        // File inputs are often hidden, so skip hover and directly upload
        try {
          // Wait for file input to be available
          await page.waitForSelector(selector, { state: 'attached', timeout: 5000 });
          
          // Check if file input is visible or hidden
          const isVisible = await page.locator(selector).isVisible().catch(() => false);
          
          if (!isVisible) {
            // For hidden file inputs, we need to make them visible temporarily
            await page.evaluate((sel: string) => {
              const el = document.querySelector(sel) as HTMLInputElement;
              if (el) {
                // Store original style
                (el as any).__originalStyle = el.style.cssText;
                // Make visible temporarily
                el.style.position = 'absolute';
                el.style.visibility = 'visible';
                el.style.opacity = '1';
                el.style.width = '1px';
                el.style.height = '1px';
              }
            }, selector);
          }
          
          // Upload the file
          await page.setInputFiles(selector, filePath);
          console.log(`    ✅ File uploaded successfully`);
          
          // Wait for upload to complete (some forms show progress)
          await page.waitForTimeout(2000);
          
          // Verify file was uploaded - try multiple selector strategies
          // Note: Some forms (like Greenhouse) replace file inputs after upload, so verification may fail
          // even though the upload succeeded. The "File uploaded successfully" message from setInputFiles
          // is the primary indicator of success.
          let uploadVerification: any = { uploaded: false, reason: 'Not checked yet' };
          
          // Strategy 1: Try the original selector
          try {
            uploadVerification = await page.evaluate(({ sel, name, dataQa }: { sel: string; name?: string; dataQa?: string }) => {
              // Try multiple selector strategies
              let el: HTMLInputElement | null = null;
              
              // Try original selector
              el = document.querySelector(sel) as HTMLInputElement;
              
              // Try by name if original failed
              if (!el && name) {
                el = document.querySelector(`input[type="file"][name="${name}"]`) as HTMLInputElement;
              }
              
              // Try by data-qa if still not found
              if (!el && dataQa) {
                el = document.querySelector(`input[type="file"][data-qa="${dataQa}"]`) as HTMLInputElement;
              }
              
              // Try any file input if still not found
              if (!el) {
                const fileInputs = document.querySelectorAll('input[type="file"]');
                el = fileInputs[fileInputs.length - 1] as HTMLInputElement; // Get last one (most recent)
              }
              
              if (!el) return { 
                uploaded: false, 
                reason: 'Element not found with any strategy',
                elementFound: false,
                triedSelectors: [sel, name ? `input[type="file"][name="${name}"]` : null, dataQa ? `input[type="file"][data-qa="${dataQa}"]` : null].filter(Boolean)
              };
              
              const hasFiles = el.files && el.files.length > 0;
              const fileName = hasFiles && el.files ? el.files[0].name : '';
              const fileSize = hasFiles && el.files ? el.files[0].size : 0;
              const hasValue = el.value && el.value.trim() !== '';
              
              return {
                uploaded: !!(hasFiles || hasValue), // Ensure boolean
                hasFiles: !!hasFiles,
                hasValue: !!hasValue,
                fileName,
                fileSize,
                value: el.value || '',
                selector: sel,
                elementFound: true
              };
            }, { sel: selector, name: field.name, dataQa: field.dataQa });
          } catch (e) {
            uploadVerification = { uploaded: false, reason: `Error during verification: ${e}` };
          }
          
          if (uploadVerification.uploaded) {
            console.log(`    ✅ File upload verified`);
            if (uploadVerification.hasFiles) {
              console.log(`    📄 File: ${uploadVerification.fileName} (${uploadVerification.fileSize} bytes)`);
            }
          } else {
            // Verification failed, but upload may still have succeeded
            // Some forms replace file inputs after upload, making verification difficult
            if (uploadVerification.elementFound === false) {
              console.log(`    ⚠️  File input element not found after upload (may have been replaced by form framework)`);
              console.log(`    ℹ️  This is normal for some forms - upload likely succeeded if no error occurred`);
            } else {
              console.log(`    ⚠️  File upload verification failed:`, {
                hasFiles: uploadVerification.hasFiles,
                hasValue: uploadVerification.hasValue,
                value: uploadVerification.value?.substring(0, 50)
              });
            }
            
            // Try alternative verification - check if form shows file name in nearby elements
            if (!uploadVerification.uploaded) {
              try {
              const alternativeCheck = await page.evaluate(({ name, dataQa }: { name?: string; dataQa?: string }) => {
                // Find file input by name or data-qa
                let el: HTMLInputElement | null = null;
                if (name) {
                  el = document.querySelector(`input[type="file"][name="${name}"]`) as HTMLInputElement;
                } else if (dataQa) {
                  el = document.querySelector(`input[type="file"][data-qa="${dataQa}"]`) as HTMLInputElement;
                } else {
                  // Get all file inputs and check the last one
                  const fileInputs = document.querySelectorAll('input[type="file"]');
                  el = fileInputs[fileInputs.length - 1] as HTMLInputElement;
                }
                
                if (!el) return { hasFileName: false, reason: 'No file input found' };
                
                // Check container for file name indicators
                const container = el.closest('div, form, fieldset, label');
                const containerText = container?.textContent || '';
                
                // Also check siblings
                const parent = el.parentElement;
                const siblingsText = parent?.textContent || '';
                
                // Look for file name indicators (PDF, DOC, file extensions, or "attached" text)
                const hasFileName = /\.(pdf|doc|docx|txt|rtf)/i.test(containerText + siblingsText) ||
                                   /(attached|uploaded|selected|file)/i.test(containerText + siblingsText);
                
                return {
                  hasFileName,
                  containerText: (containerText + siblingsText).substring(0, 150),
                  hasFiles: el.files && el.files.length > 0,
                  value: el.value
                };
              }, { name: field.name, dataQa: field.dataQa });
              
              if (alternativeCheck.hasFileName || alternativeCheck.hasFiles) {
                console.log(`    ✅ File upload verified via alternative method`);
                if (alternativeCheck.hasFiles) {
                  console.log(`    📄 File input has files attached`);
                }
              } else {
                console.log(`    ⚠️  Could not verify file upload - but upload may have succeeded`);
                console.log(`    📋 Container text: ${alternativeCheck.containerText}`);
              }
              } catch (altError) {
                console.log(`    ⚠️  Alternative verification also failed: ${altError}`);
              }
            }
          }
          
          // Restore original style if we modified it
          if (!isVisible) {
            await page.evaluate((sel: string) => {
              const el = document.querySelector(sel) as HTMLInputElement;
              if (el && (el as any).__originalStyle !== undefined) {
                el.style.cssText = (el as any).__originalStyle;
              }
            }, selector);
          }
        } catch (uploadError: any) {
          console.log(`    ❌ Upload failed: ${uploadError.message}`);
          // Don't throw - continue with other fields
        } finally {
          // Clean up temp file after a delay to ensure upload completed
          if (tempFile && filePath) {
            // Wait a bit longer before cleanup to ensure upload is processed
            setTimeout(() => {
              cleanup(filePath);
            }, 3000); // 3 second delay
          }
        }
        break;
      
      default:
        console.log(`    ⚠️ Unknown field type: ${type}`);
    }
    
    // Small delay after filling for realism (shorter for phone/email/number fields)
    if (type === 'tel' || type === 'email' || type === 'number') {
      await page.waitForTimeout(100);
    } else {
      await page.waitForTimeout(500);
    }
    
  } catch (error: any) {
    console.log(`    ❌ Error filling field: ${error.message}`);
  }
}

/**
 * Main function: Fill all form fields
 */
export async function fillForm(page: any, fields: FormField[], profile: JobProfile): Promise<void> {
  console.log(`\n📝 Filling ${fields.length} form fields...`);
  
  // STEP 1: Pre-fetch all AI answers in parallel BEFORE filling any fields
  console.log(`\n🤖 Pre-fetching AI answers for unmapped fields...`);
  const fieldValues = new Map<FormField, string | null>();
  const aiPromises: Promise<void>[] = [];
  
  for (const field of fields) {
    let value = mapProfileToField(field.inferredPurpose, profile);
    
    // If no direct mapping and needs AI, prepare the API call
    if ((value === null || value === undefined || value === '') && field.inferredPurpose === 'custom') {
      // Skip hidden fields, captcha, and non-interactive elements
      if (field.name?.toLowerCase().includes('captcha') || 
          field.name?.toLowerCase().includes('g-recaptcha') ||
          field.name?.toLowerCase().includes('hidden') ||
          !field.label && !field.placeholder) {
        fieldValues.set(field, null);
        continue;
      }
      
      // For required fields or fields with meaningful labels, prepare AI call
      if (field.required || (field.label && field.label.trim().length > 3)) {
        const label = (field.label || '').toLowerCase();
        let options = field.options ? 
          field.options.map((opt: any) => typeof opt === 'string' ? opt : opt.text || opt.value || opt.label).filter(Boolean) :
          undefined;
        
        // Make AI call in parallel
        const aiPromise = getIntelligentAnswer(field, profile, options).then(aiValue => {
          if (!aiValue) {
            aiValue = getSmartFallback(field, profile);
          }
          fieldValues.set(field, aiValue);
        }).catch(() => {
          // If AI fails, use fallback
          const fallbackValue = getSmartFallback(field, profile);
          fieldValues.set(field, fallbackValue);
        });
        aiPromises.push(aiPromise);
      } else {
        fieldValues.set(field, null);
      }
    } else {
      fieldValues.set(field, value);
    }
  }
  
  // Wait for all AI calls to complete
  if (aiPromises.length > 0) {
    console.log(`  ⏳ Waiting for ${aiPromises.length} AI answer(s)...`);
    await Promise.all(aiPromises);
    console.log(`  ✅ All AI answers received!\n`);
  }
  
  // STEP 2: Sort fields - basic text fields first, then others
  const sortedFields = [...fields].sort((a, b) => {
    // Basic text fields: text, tel, email, url, number, textarea
    const aIsBasic = ['text', 'tel', 'email', 'url', 'number', 'textarea'].includes(a.type);
    const bIsBasic = ['text', 'tel', 'email', 'url', 'number', 'textarea'].includes(b.type);
    
    if (aIsBasic && !bIsBasic) return -1; // Basic fields first
    if (!aIsBasic && bIsBasic) return 1;
    return 0; // Keep original order within same category
  });
  
  // STEP 3: Fill all fields with pre-fetched values
  // Track previous field answers for conditional fields
  const fieldAnswers = new Map<string, string>();
  
  for (const field of sortedFields) {
    // Check if this is a conditional field that needs special handling
    const label = (field.label || '').toLowerCase();
    let conditionalValue = null;
    
    if (/if yes|if.*yes|conditional|depends on/i.test(label)) {
      // Check for "If yes, what County within Ireland?" pattern
      if (/county.*ireland|if.*yes.*county/i.test(label)) {
        // Look for the "Are you currently located in Ireland?" question
        for (const [fieldName, answer] of fieldAnswers.entries()) {
          if (/ireland.*located|located.*ireland/i.test(fieldName.toLowerCase())) {
            if (answer.toLowerCase() === 'no' || answer.toLowerCase() === 'false') {
              // Instead of skipping, set a default value like "Not applicable"
              conditionalValue = 'Not applicable - I do not live in Ireland';
              console.log(`  📝 Conditional field detected: "${field.label}" - will use default value since previous answer was "No"`);
              break;
            }
          }
        }
      }
    }
    
    // Get pre-fetched value or use direct mapping
    let value = fieldValues.get(field);
    if (value === undefined) {
      value = mapProfileToField(field.inferredPurpose, profile);
    }
    
    // Use conditional value if set
    if (conditionalValue) {
      value = conditionalValue;
    }
    
    // Handle required checkbox groups first - auto-select if no value
    if (field.type === 'checkbox-group' && field.required && (!value || (Array.isArray(value) && value.length === 0))) {
      console.log(`  📋 Required checkbox group: "${field.label || field.name}" - auto-selecting first option`);
      await fillField(page, field, null); // Pass null to trigger auto-selection in fillField
      continue;
    }
    
    // Skip hidden fields, captcha, and non-interactive elements
    if (field.name?.toLowerCase().includes('captcha') || 
        field.name?.toLowerCase().includes('g-recaptcha') ||
        field.name?.toLowerCase().includes('hidden') ||
        (!field.label && !field.placeholder && !value)) {
      console.log(`  ⏭️ Skipping: ${field.name || 'unnamed field'} (hidden/captcha field)`);
      continue;
    }
    
    // Final check - if still no value and field is required, use smart fallback
    if ((value === null || value === undefined || value === '') && field.required) {
      value = getSmartFallback(field, profile);
    }
    
    if (value === null || value === undefined || value === '') {
      console.log(`  ⏭️ Skipping: ${field.label || field.name} (no value available)`);
      continue;
    }
    
    // Store the answer for conditional field checking
    const fieldKey = field.label || field.name || '';
    if (fieldKey) {
      fieldAnswers.set(fieldKey, String(value));
    }
    
    await fillField(page, field, value);
  }
  
  console.log('\n✅ Form filling complete!');
}

/**
 * Get smart fallback answer based on field context when AI is not available
 */
function getSmartFallback(field: FormField, profile: JobProfile): string | null {
  const label = (field.label || field.placeholder || field.name || '').toLowerCase();
  const fieldType = field.type;
  
  // Location-related questions
  if (/ireland|located|location|county|where.*live|where.*based/i.test(label)) {
    if (/ireland/i.test(label)) {
      return profile.country === 'Ireland' ? 'Yes' : 'No';
    }
    if (/county/i.test(label) && profile.country === 'Ireland') {
      return profile.city || profile.state || 'Dublin';
    }
    return [profile.city, profile.state, profile.country].filter(Boolean).join(', ') || null;
  }
  
  // Yes/No questions - default to positive for eligibility
  if (fieldType === 'select' || fieldType === 'radio-group') {
    if (/eligible|authorized|willing|able|can|have/i.test(label)) {
      return 'Yes';
    }
    if (/require.*sponsor|need.*visa/i.test(label)) {
      return profile.requiresSponsorship ? 'Yes' : 'No';
    }
  }
  
  // Experience-related
  if (/experience|years|how long/i.test(label)) {
    if (profile.yearsOfExperience) {
      return String(profile.yearsOfExperience);
    }
  }
  
  // Education-related
  if (/education|degree|university|school|college/i.test(label)) {
    if (/degree|qualification/i.test(label)) {
      return profile.highestDegree || 'Bachelor\'s Degree';
    }
    if (/university|school|college/i.test(label)) {
      return profile.university || '';
    }
  }
  
  // Skills-related
  if (/skill|technology|expertise|proficient/i.test(label)) {
    return profile.technicalSkills || '';
  }
  
  // Availability/Start date
  if (/available|start|when.*begin|notice/i.test(label)) {
    return profile.availableStartDate || 'Immediately available';
  }
  
  // Why/Interest questions
  if (/why|interest|motivated|excited|drawn/i.test(label)) {
    return profile.whyThisCompany || 
           `I'm excited about this opportunity because it aligns with my ${profile.yearsOfExperience || 'extensive'} years of experience in ${profile.currentJobTitle || 'my field'}.`;
  }
  
  // About/Describe questions
  if (/about|describe|tell.*about|introduce/i.test(label)) {
    const parts = [];
    if (profile.currentJobTitle) parts.push(`I'm a ${profile.currentJobTitle}`);
    if (profile.currentCompany) parts.push(`at ${profile.currentCompany}`);
    if (profile.yearsOfExperience) parts.push(`with ${profile.yearsOfExperience} years of experience`);
    if (profile.technicalSkills) parts.push(`specializing in ${profile.technicalSkills.split(',')[0]}`);
    return parts.length > 0 ? parts.join(' ') + '.' : null;
  }
  
  return null;
}