export type FieldType = 'text' | 'email' | 'tel' | 'number' | 'url' | 'textarea' | 'select' | 'radio' | 'radio-group' | 'checkbox' | 'checkbox-group' | 'file';

/**
 * Regex pattern for field recognition
 */
interface FieldPattern {
  patterns: RegExp[];
  purpose: InferredPurpose;
  priority: number;
  valueExtractor?: (profile: JobProfile) => any;
}

/**
 * Comprehensive field patterns for regex-based mapping
 */
const FIELD_PATTERNS: FieldPattern[] = [
  // === PERSONAL INFORMATION ===
  {
    patterns: [/^first[\s_-]?name$/i, /^fname$/i, /^first$/i, /firstname/i, /inputfirst/i, /name\[first\]/i],
    purpose: 'firstName',
    priority: 100
  },
  {
    patterns: [/^preferred[\s_-]?first[\s_-]?name$/i, /^preferred[\s_-]?name$/i, /^pref[\s_-]?first[\s_-]?name$/i, /^nickname$/i, /^preferred$/i],
    purpose: 'firstName', // Preferred first name defaults to first name
    priority: 95
  },
  {
    patterns: [/^last[\s_-]?name$/i, /^lname$/i, /^last$/i, /lastname/i, /inputlast/i, /name\[last\]/i, /surname/i],
    purpose: 'lastName',
    priority: 100
  },
  {
    patterns: [/^(full[\s_-]?name|name)$/i, /^your[\s_-]?name$/i, /^applicant[\s_-]?name$/i],
    purpose: 'fullName',
    priority: 80,
    valueExtractor: (profile) => `${profile.firstName} ${profile.lastName}`.trim()
  },
  
  // === CONTACT INFORMATION ===
  {
    patterns: [/^email$/i, /^e-?mail/i, /^email[\s_-]?address$/i, /inputemail/i, /email\[/i],
    purpose: 'email',
    priority: 100
  },
  {
    patterns: [/^phone$/i, /^telephone$/i, /^mobile$/i, /^phone[\s_-]?(number|no)/i, /^contact[\s_-]?number$/i, /inputphone/i, /^tel$/i],
    purpose: 'phone',
    priority: 100
  },
  
  // === LOCATION ===
  {
    patterns: [/^address$/i, /^street[\s_-]?address$/i, /^address[\s_-]?line/i],
    purpose: 'address',
    priority: 100
  },
  {
    patterns: [/^city$/i, /town/i],
    purpose: 'city',
    priority: 100
  },
  {
    patterns: [/^state$/i, /^province$/i, /^region$/i],
    purpose: 'state',
    priority: 100
  },
  {
    patterns: [/^(zip|postal)[\s_-]?code$/i, /^postcode$/i, /^zip$/i],
    purpose: 'zipCode',
    priority: 100
  },
  {
    patterns: [/^country$/i, /^nation$/i],
    purpose: 'country',
    priority: 100
  },
  
  // === PROFESSIONAL ===
  {
    patterns: [/current[\s_-]?(job[\s_-]?)?title/i, /^job[\s_-]?title$/i, /^title$/i, /^position$/i, /^role$/i],
    purpose: 'currentJobTitle',
    priority: 90
  },
  {
    patterns: [/current[\s_-]?company/i, /current[\s_-]?employer/i, /^company$/i, /^employer$/i, /^organization$/i, /^org$/i],
    purpose: 'currentCompany',
    priority: 90
  },
  {
    patterns: [/years?[\s_-]?(of[\s_-]?)?experience/i, /experience[\s_-]?years/i, /total[\s_-]?experience/i],
    purpose: 'yearsOfExperience',
    priority: 90
  },
  
  // === SOCIAL/PROFESSIONAL LINKS ===
  {
    patterns: [/linkedin/i, /linked[\s_-]?in/i, /^li[\s_-]?profile/i, /urls?\[linkedin\]/i, /question_\d+.*linkedin/i],
    purpose: 'linkedinUrl',
    priority: 100
  },
  {
    patterns: [/github/i, /git[\s_-]?hub/i, /urls?\[github\]/i],
    purpose: 'githubUrl',
    priority: 100
  },
  {
    patterns: [/portfolio/i, /personal[\s_-]?website/i, /^website$/i, /urls?\[(portfolio|other|website)\]/i],
    purpose: 'portfolioUrl',
    priority: 90
  },
  
  // === EDUCATION ===
  {
    patterns: [/^degree$/i, /education[\s_-]?level/i, /highest[\s_-]?degree/i, /qualification/i],
    purpose: 'highestDegree',
    priority: 90
  },
  {
    patterns: [/field[\s_-]?of[\s_-]?study/i, /major/i, /specialization/i, /course/i],
    purpose: 'fieldOfStudy',
    priority: 90
  },
  {
    patterns: [/university/i, /college/i, /school/i, /institution/i],
    purpose: 'university',
    priority: 85
  },
  {
    patterns: [/graduation[\s_-]?year/i, /year[\s_-]?(of[\s_-]?)?graduation/i, /completed[\s_-]?year/i],
    purpose: 'graduationYear',
    priority: 90
  },
  {
    patterns: [/\bgpa\b/i, /grade[\s_-]?point/i],
    purpose: 'gpa',
    priority: 90
  },
  
  // === WORK AUTHORIZATION ===
  {
    patterns: [/work[\s_-]?authorization/i, /legally[\s_-]?authorized/i, /authorized[\s_-]?to[\s_-]?work/i, /eligible[\s_-]?to[\s_-]?work/i],
    purpose: 'workAuthorization',
    priority: 95
  },
  {
    patterns: [/require.*sponsor/i, /visa[\s_-]?sponsor/i, /need.*sponsor/i, /employment.*sponsor/i],
    purpose: 'requiresSponsorship',
    priority: 95,
    valueExtractor: (profile) => profile.requiresSponsorship ? 'Yes' : 'No'
  },
  
  // === RELOCATION ===
  {
    patterns: [/willing[\s_-]?to[\s_-]?relocate/i, /able[\s_-]?to[\s_-]?relocate/i, /open[\s_-]?to[\s_-]?relocation/i],
    purpose: 'willingToRelocate',
    priority: 95,
    valueExtractor: (profile) => profile.willingToRelocate ? 'Yes' : 'No'
  },
  {
    patterns: [/location[\s_-]?preference/i, /preferred[\s_-]?location/i],
    purpose: 'preferredWorkLocation',
    priority: 85
  },
  
  // === SALARY ===
  {
    patterns: [/expected[\s_-]?salary/i, /desired[\s_-]?salary/i, /salary[\s_-]?expectation/i, /compensation/i],
    purpose: 'expectedSalary',
    priority: 90
  },
  {
    patterns: [/current[\s_-]?salary/i, /present[\s_-]?salary/i],
    purpose: 'currentSalary',
    priority: 90
  },
  
  // === AVAILABILITY ===
  {
    patterns: [/notice[\s_-]?period/i, /availability/i, /start[\s_-]?date/i, /joining[\s_-]?date/i, /when[\s_-]?can[\s_-]?you[\s_-]?start/i],
    purpose: 'availableStartDate',
    priority: 85
  },
  
  // === ADDITIONAL INFO ===
  {
    patterns: [/cover[\s_-]?letter/i, /additional[\s_-]?information/i, /comments/i, /message/i, /tell[\s_-]?us[\s_-]?(more|about)/i, /why[\s_-]?/i],
    purpose: 'whyThisCompany',
    priority: 70
  },
  
  // === DIVERSITY/EEO ===
  {
    patterns: [/gender/i, /\bsex\b/i],
    purpose: 'gender',
    priority: 80
  },
  {
    patterns: [/veteran/i, /military/i],
    purpose: 'veteranStatus',
    priority: 80
  },
  {
    patterns: [/disability/i, /disabled/i],
    purpose: 'disabilityStatus',
    priority: 80
  },
  {
    patterns: [/race/i, /racial/i, /ethnicity/i, /ethnic/i],
    purpose: 'race',
    priority: 80
  },
  
  // === SKILLS ===
  {
    patterns: [/technical[\s_-]?skills/i, /skills/i, /technologies/i],
    purpose: 'technicalSkills',
    priority: 75
  },
  {
    patterns: [/certifications?/i],
    purpose: 'certifications',
    priority: 75
  },
  
  // === REFERRAL ===
  {
    patterns: [/hear[\s_-]?about[\s_-]?us/i, /how[\s_-]?did[\s_-]?you[\s_-]?hear/i, /referral/i, /referred[\s_-]?by/i],
    purpose: 'referralSource',
    priority: 70
  }
];

export type InferredPurpose =
  | 'firstName'
  | 'lastName'
  | 'fullName'
  | 'email'
  | 'phone'
  | 'address'
  | 'city'
  | 'state'
  | 'zipCode'
  | 'country'
  | 'currentCompany'
  | 'currentJobTitle'
  | 'yearsOfExperience'
  | 'linkedinUrl'
  | 'githubUrl'
  | 'portfolioUrl'
  | 'websiteUrl'
  | 'highestDegree'
  | 'university'
  | 'graduationYear'
  | 'fieldOfStudy'
  | 'gpa'
  | 'expectedSalary'
  | 'currentSalary'
  | 'noticePeriod'
  | 'workAuthorization'
  | 'requiresSponsorship'
  | 'willingToRelocate'
  | 'preferredWorkLocation'
  | 'availableStartDate'
  | 'technicalSkills'
  | 'certifications'
  | 'resume'
  | 'coverLetter'
  | 'whyThisCompany'
  | 'careerGoals'
  | 'referralSource'
  | 'hearAboutUs'
  | 'veteranStatus'
  | 'disabilityStatus'
  | 'gender'
  | 'race'
  | 'custom';

export interface FormField {
  selector: string;
  type: FieldType;
  label: string;
  required: boolean;
  placeholder?: string;
  options?: string[];
  inferredPurpose?: InferredPurpose;
  name?: string;
  dataQa?: string;
  isAutocomplete?: boolean;
}

export interface JobProfile {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  currentCompany?: string;
  currentJobTitle?: string;
  yearsOfExperience?: number;
  linkedinUrl?: string;
  githubUrl?: string;
  portfolioUrl?: string;
  websiteUrl?: string;
  highestDegree?: string;
  university?: string;
  graduationYear?: number;
  fieldOfStudy?: string;
  gpa?: string;
  expectedSalary?: string;
  currentSalary?: string;
  noticePeriod?: string;
  workAuthorization?: string;
  requiresSponsorship?: boolean;
  willingToRelocate?: boolean;
  preferredWorkLocation?: string;
  availableStartDate?: string;
  technicalSkills?: string;
  certifications?: string;
  resumeUrl?: string;
  coverLetterUrl?: string;
  whyThisCompany?: string;
  careerGoals?: string;
  referralSource?: string;
  veteranStatus?: string;
  disabilityStatus?: string;
  gender?: string;
  race?: string;
}

/**
 * Get form elements from the page with enhanced detection
 */
async function getFormElements(page: any): Promise<any[]> {
  return await page.evaluate(() => {
    const fields: any[] = [];
    const inputs = document.querySelectorAll('input, select, textarea, [role="combobox"], [role="listbox"]');
    
    // Group radio buttons and checkboxes
    const radioGroups = new Map<string, any[]>();
    const checkboxGroups = new Map<string, any[]>();
    
    inputs.forEach((element: any, index: number) => {
      // Skip hidden inputs
      if (element.type === 'hidden') return;
      
      // Generate unique selector - escape special characters in IDs
      let selector = '';
      if (element.id) {
        // Escape special CSS selector characters in ID (like numbers starting with digit)
        // If ID starts with a digit or contains special chars, use attribute selector
        const id = element.id;
        if (/^[0-9]/.test(id) || /[!"#$%&'()*+,.\/:;<=>?@[\\\]^`{|}~]/.test(id)) {
          selector = `[id="${id}"]`;
        } else {
          selector = `#${id}`;
        }
      } else if (element.name) {
        selector = `[name="${element.name}"]`;
      } else {
        selector = `${element.tagName.toLowerCase()}:nth-of-type(${index + 1})`;
      }
      
      // Get label with enhanced detection
      let label = '';
      if (element.id) {
        const labelEl = document.querySelector(`label[for="${element.id}"]`);
        if (labelEl) label = labelEl.textContent?.trim() || '';
      }
      if (!label) {
        const parentLabel = element.closest('label');
        if (parentLabel) label = parentLabel.textContent?.trim() || '';
      }
      if (!label) {
        const container = element.closest('.application-question, .form-field, .field-container');
        if (container) {
          const labelEl = container.querySelector('.application-label, .field-label, label, .text');
          if (labelEl) label = labelEl.textContent?.trim() || '';
        }
      }
      
      const name = element.name || element.id || '';
      const type = element.type || element.tagName.toLowerCase();
      const required = element.required || element.getAttribute('aria-required') === 'true';
      const placeholder = element.placeholder || '';
      const dataQa = element.getAttribute('data-qa') || '';
      
      // Handle radio buttons - group them
      if (type === 'radio') {
        const group = radioGroups.get(name) || [];
        group.push({
          value: element.value,
          label: label || element.nextSibling?.textContent?.trim() || element.value,
          checked: element.checked
        });
        radioGroups.set(name, group);
        return;
      }
      
      // Handle checkboxes - detect if grouped
      if (type === 'checkbox') {
        const container = element.closest('[data-qa*="Checkboxes"], .checkbox-group, .multiple-select');
        if (container || (name && name !== 'consent[marketing]')) {
          const groupName = name || container?.getAttribute('data-qa') || 'checkbox-group';
          const group = checkboxGroups.get(groupName) || [];
          group.push({
            value: element.value,
            label: label || element.nextSibling?.textContent?.trim() || element.value,
            checked: element.checked,
            name: name
          });
          checkboxGroups.set(groupName, group);
          return;
        }
      }
      
      // Get options for select elements
      let options: string[] = [];
      if (element.tagName === 'SELECT') {
        options = Array.from(element.options).map((opt: any) => opt.text);
      }
      
      // Detect if it's an autocomplete field (dropdown-like)
      // BUT exclude phone/tel fields - they should never be autocomplete
      const isPhoneField = type === 'tel' || /phone|telephone|mobile/i.test(name + ' ' + label);
      const isAutocomplete = !isPhoneField && (
                            type === 'select' || 
                            /country|location|state|city|company|university|school|ireland|county|sponsorship|visa|authorization|eligibility|yes|no/i.test(name + ' ' + label) ||
                            element.getAttribute('role') === 'combobox' ||
                            element.getAttribute('aria-haspopup') === 'listbox' ||
                            element.closest('[role="combobox"]') !== null);
      
      fields.push({
        selector,
        name,
        type,
        label: label || placeholder || name || '',
        required,
        placeholder,
        dataQa,
        options: options.length > 0 ? options : undefined,
        isAutocomplete
      });
    });
    
    // Add grouped radio buttons
    radioGroups.forEach((options, name) => {
      fields.push({
        selector: `[name="${name}"]`,
        name,
        type: 'radio-group',
        options: options,
        required: document.querySelector(`input[name="${name}"][required]`) !== null,
        label: options[0]?.label?.replace(options[0]?.value, '')?.trim() || name,
        isAutocomplete: false
      });
    });
    
    // Add grouped checkboxes
    checkboxGroups.forEach((options, name) => {
      // Check if any checkbox in the group is required
      const isRequired = document.querySelector(`input[name="${name}"][required]`) !== null ||
                        document.querySelector(`fieldset[id="${name}"][aria-required="true"]`) !== null ||
                        document.querySelector(`fieldset:has(input[name="${name}"][required])`) !== null;
      
      // Get label from fieldset legend if available
      let groupLabel = name;
      const fieldset = document.querySelector(`fieldset:has(input[name="${name}"])`);
      if (fieldset) {
        const legend = fieldset.querySelector('legend');
        if (legend) {
          groupLabel = legend.textContent?.trim() || name;
        }
      }
      
      fields.push({
        selector: `[name="${name}"]`,
        name,
        type: 'checkbox-group',
        options: options,
        required: isRequired,
        label: groupLabel,
        isAutocomplete: false
      });
    });
    
    return fields;
  });
}

/**
 * Map field to profile using regex patterns
 */
function mapFieldToProfile(field: any, profile: JobProfile): InferredPurpose | undefined {
  // Get all identifiers for this field
  const identifiers = [
    field.name,
    field.label,
    field.placeholder,
    field.dataQa
  ].filter(Boolean).map(id => id.toLowerCase());
  
  let bestMatch: FieldPattern | null = null;
  let highestPriority = -1;
  
  // Test each identifier against all patterns
  for (const identifier of identifiers) {
    for (const pattern of FIELD_PATTERNS) {
      for (const regex of pattern.patterns) {
        if (regex.test(identifier)) {
          if (pattern.priority > highestPriority) {
            highestPriority = pattern.priority;
            bestMatch = pattern;
          }
        }
      }
    }
  }
  
  // Special handling for file upload fields
  if (field.type === 'file') {
    const fieldText = identifiers.join(' ');
    if (/resume|cv/i.test(fieldText)) {
      return 'resume';
    }
    if (/cover[\s_-]?letter/i.test(fieldText)) {
      return 'coverLetter';
    }
  }
  
  return bestMatch ? bestMatch.purpose : 'custom';
}

/**
 * Analyze fields using regex-based pattern matching
 */
function analyzeWithRegex(fields: any[], profile: JobProfile): FormField[] {
  const analyzedFields: FormField[] = [];
  
  for (const field of fields) {
    // Infer field type more accurately
    let fieldType = field.type;
    const fieldText = (field.name + ' ' + field.label + ' ' + field.placeholder).toLowerCase();
    
    if (fieldType === 'text' || fieldType === 'input') {
      if (/email/i.test(fieldText)) {
        fieldType = 'email';
      } else if (/phone|tel|mobile/i.test(fieldText)) {
        fieldType = 'tel';
      } else if (/salary|year|experience|gpa|number|days/i.test(fieldText)) {
        fieldType = 'number';
      } else if (/url|link|website|linkedin|github|portfolio/i.test(fieldText)) {
        fieldType = 'url';
      }
    }
    
    // Map to profile
    const inferredPurpose = mapFieldToProfile(field, profile);
    
    // Clean label
    const label = (field.label || '')
      .replace(/\s*[✱*]\s*$/g, '')
      .trim();
    
    analyzedFields.push({
      selector: field.selector,
      name: field.name,
      type: fieldType,
      label: label || field.placeholder || field.name,
      required: field.required,
      placeholder: field.placeholder,
      options: field.options,
      inferredPurpose,
      dataQa: field.dataQa,
      isAutocomplete: field.isAutocomplete
    });
  }
  
  console.log('✅ Regex Analysis Complete:', analyzedFields.length, 'fields analyzed');
  return analyzedFields;
}

/**
 * Main function: Analyze form and return mapped fields
 */
export async function analyzeForm(page: any, profile: JobProfile): Promise<FormField[]> {
  console.log('🔍 Analyzing form structure...');
  
  console.log('📋 Getting form elements...');
  const fields = await getFormElements(page);
  console.log(`Found ${fields.length} form fields`);
  
  console.log('🎯 Mapping fields with regex patterns...');
  const analyzedFields = analyzeWithRegex(fields, profile);
  
  // Log mapping summary
  const mappedCount = analyzedFields.filter(f => f.inferredPurpose && f.inferredPurpose !== 'custom').length;
  const autocompleteCount = analyzedFields.filter(f => f.isAutocomplete).length;
  console.log(`✅ Mapped ${mappedCount}/${fields.length} fields`);
  if (autocompleteCount > 0) {
    console.log(`⚠️  Found ${autocompleteCount} autocomplete fields (require special handling)`);
  }
  
  return analyzedFields;
}