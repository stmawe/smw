(function () {
  const configEl = document.getElementById('wizard-config');
  if (!configEl) {
    return;
  }

  const config = JSON.parse(configEl.textContent);
  const shell = document.getElementById('shop-wizard-shell');
  const form = document.getElementById('shop-wizard-form');
  const stepPanels = Array.from(document.querySelectorAll('[data-step-panel]'));
  const stepperItems = Array.from(document.querySelectorAll('[data-step-jump]'));
  const prevButton = document.querySelector('[data-step-prev]');
  const nextButton = document.querySelector('[data-step-next]');
  const submitButton = document.querySelector('[data-step-submit]');
  const previewShell = document.querySelector('[data-preview-shell]');
  const previewToggle = document.querySelector('[data-preview-toggle]');
  const slugInput = document.getElementById('shop-slug');
  const slugPreview = document.querySelector('[data-slug-preview]');
  const slugStatus = document.querySelector('[data-slug-status]');
  const previewName = document.querySelector('[data-preview-name]');
  const previewShop = document.querySelector('[data-preview-shop]');
  const previewSlug = document.querySelector('[data-preview-slug]');
  const previewCategory = document.querySelector('[data-preview-category]');
  const previewAffiliation = document.querySelector('[data-preview-affiliation]');
  const previewThemeLabel = document.querySelector('[data-preview-theme-label]');
  const previewDescription = document.querySelector('[data-preview-description]');
  const previewWhatsapp = document.querySelector('[data-preview-whatsapp]');
  const previewLogo = document.querySelector('[data-preview-logo]');
  const previewBanner = document.querySelector('[data-preview-banner]');
  const previewLogoText = document.querySelector('[data-preview-logo-text]');
  const reviewName = document.querySelector('[data-review-name]');
  const reviewSlug = document.querySelector('[data-review-slug]');
  const reviewCategory = document.querySelector('[data-review-category]');
  const reviewTheme = document.querySelector('[data-review-theme]');
  const reviewWhatsapp = document.querySelector('[data-review-whatsapp]');
  const descriptionCount = document.querySelector('[data-description-count]');
  const verificationEmailInput = document.getElementById('verification-email');
  const verificationCodeInput = document.getElementById('verification-code');
  const emailSendButton = document.querySelector('[data-email-send]');
  const emailVerifyButton = document.querySelector('[data-email-verify]');
  const emailState = document.querySelector('[data-email-state]');
  const emailVerifiedFlag = document.querySelector('[data-email-verified-flag]');
  const paymentPhoneInput = document.getElementById('payment-phone');
  const paymentStatePanel = document.querySelector('[data-payment-state-panel]');
  const paymentStateLabel = document.querySelector('[data-payment-state-label]');
  const paymentStateCopy = document.querySelector('[data-payment-state-copy]');
  const paymentRetryButton = document.querySelector('[data-payment-retry]');
  const paymentChangeNumberButton = document.querySelector('[data-payment-change-number]');
  const themeIdInput = document.getElementById('theme-id');
  const accentInput = document.getElementById('accent-color');
  const bannerPresetInput = document.getElementById('banner-preset');
  const affiliationModeInput = document.getElementById('affiliation-mode');

  const storageKey = 'smw.shopWizardState';
  const defaultTheme = config.themes.find((theme) => theme.id === 'dark_noir') || config.themes[0];
  const defaultAccent = config.accent_colors[0];
  const defaultBanner = config.banner_presets[0];
  const bannerGradients = {
    'navy-gradient': 'linear-gradient(135deg, #020A1A 0%, #0D3366 60%, #1050A0 100%)',
    'gold-glow': 'linear-gradient(135deg, #1A1000 0%, #3D2800 50%, #9B6400 100%)',
    'green-forest': 'linear-gradient(135deg, #011208 0%, #064A20 60%, #0F9640 100%)',
    mosaic: 'conic-gradient(from 45deg, #020A1A, #0D3366, #C9920A, #0A6B2D, #020A1A)',
  };

  const defaultState = {
    step: 1,
    themeId: defaultTheme ? defaultTheme.id : 'dark_noir',
    accentColor: defaultAccent ? defaultAccent.value : '#1A72E8',
    bannerPreset: defaultBanner ? defaultBanner.id : 'navy-gradient',
    initialsStyle: 'bold',
    affiliationMode: 'skip',
    slugStatus: 'idle',
    logoPreview: '',
    bannerPreview: '',
    fields: {},
  };

  let state = restoreState();
  let slugTimer = null;
  let slugRequestId = 0;
  let paymentPollTimer = null;
  let paymentPollDeadline = null;
  const initialPaymentState = shell ? shell.dataset.paymentState || 'idle' : 'idle';
  const initialPaymentRef = shell ? shell.dataset.paymentRef || '' : '';

  function restoreState() {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) {
        return { ...defaultState, fields: getFieldSnapshot() };
      }

      const parsed = JSON.parse(raw);
      return {
        ...defaultState,
        ...parsed,
        fields: { ...defaultState.fields, ...(parsed.fields || {}) },
      };
    } catch (error) {
      return { ...defaultState, fields: getFieldSnapshot() };
    }
  }

  function saveState() {
    window.localStorage.setItem(storageKey, JSON.stringify(state));
  }

  function getFieldSnapshot() {
    return {
      shop_name: form.elements.shop_name ? form.elements.shop_name.value : '',
      tagline: form.elements.tagline ? form.elements.tagline.value : '',
      category: getCheckedValue('category'),
      affiliation_mode_choice: getCheckedValue('affiliation_mode_choice'),
      university_id: form.elements.university_id ? form.elements.university_id.value : '',
      location_id: form.elements.location_id ? form.elements.location_id.value : '',
      verification_email: form.elements.verification_email ? form.elements.verification_email.value : '',
      description: form.elements.description ? form.elements.description.value : '',
      whatsapp: form.elements.whatsapp ? form.elements.whatsapp.value : '',
      location: form.elements.location ? form.elements.location.value : '',
      instagram: form.elements.instagram ? form.elements.instagram.value : '',
      tiktok: form.elements.tiktok ? form.elements.tiktok.value : '',
      twitter: form.elements.twitter ? form.elements.twitter.value : '',
      email_verified: emailVerifiedFlag ? emailVerifiedFlag.value === '1' || emailVerifiedFlag.value === 'true' : false,
      payment_phone: paymentPhoneInput ? paymentPhoneInput.value : '',
      terms: form.elements.terms ? form.elements.terms.checked : false,
      slug: slugInput ? slugInput.value : '',
    };
  }

  function getCheckedValue(name) {
    const checked = form.querySelector(`input[name="${name}"]:checked`);
    return checked ? checked.value : '';
  }

  function generateSlug(value) {
    return (value || '')
      .toLowerCase()
      .trim()
      .replace(/['`]/g, '')
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 48)
      .replace(/^-|-$/g, '');
  }

  function getInitials(value) {
    const initials = (value || '')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join('')
      .toUpperCase();
    return initials || 'SM';
  }

  function setSlugStatus(mode, text) {
    if (!slugStatus) {
      return;
    }

    slugStatus.dataset.status = mode;
    slugStatus.textContent = text;
  }

  function setTheme(themeId) {
    const theme = config.themes.find((item) => item.id === themeId) || defaultTheme;
    if (!theme || !previewShell) {
      return;
    }

    state.themeId = theme.id;
    themeIdInput.value = theme.id;
    previewShell.style.setProperty('--wizard-preview-bg', theme.bg);
    previewShell.style.setProperty('--wizard-preview-surface', theme.surface);
    previewShell.style.setProperty('--wizard-preview-accent', theme.accent);
    previewShell.style.setProperty('--wizard-preview-text', theme.text);
    previewShell.style.setProperty('--wizard-preview-muted', theme.accent);

    if (previewThemeLabel) {
      previewThemeLabel.textContent = theme.name;
    }

    document.querySelectorAll('input[name="theme_choice"]').forEach((input) => {
      input.checked = input.value === theme.id;
    });

    document.querySelectorAll('[data-theme-id]').forEach((card) => {
      card.classList.toggle('is-active', card.dataset.themeId === theme.id);
    });
  }

  function setAccent(value) {
    state.accentColor = value;
    accentInput.value = value;
    if (previewShell) {
      previewShell.style.setProperty('--wizard-preview-accent', value);
    }

    document.querySelectorAll('[data-accent]').forEach((button) => {
      button.classList.toggle('is-active', button.dataset.accent === value);
    });
  }

  function setBannerPreset(value) {
    state.bannerPreset = value;
    bannerPresetInput.value = value;
    if (previewBanner && !previewBanner.classList.contains('has-image')) {
      previewBanner.style.backgroundImage = bannerGradients[value] || bannerGradients['navy-gradient'];
    }
    document.querySelectorAll('[data-banner-preset]').forEach((button) => {
      button.classList.toggle('is-active', button.dataset.bannerPreset === value);
    });
  }

  function setInitialsStyle(value) {
    state.initialsStyle = value;
    if (previewLogo) {
      previewLogo.dataset.style = value;
    }
    document.querySelectorAll('[data-initials-style]').forEach((button) => {
      button.classList.toggle('is-active', button.dataset.initialsStyle === value);
    });
  }

  function setAffiliationMode(value) {
    state.affiliationMode = value;
    affiliationModeInput.value = value;
    document.querySelectorAll('input[name="affiliation_mode_choice"]').forEach((input) => {
      input.checked = input.value === value;
    });
  }

  function setPaymentState(stateName, copy) {
    if (paymentStatePanel) {
      paymentStatePanel.dataset.state = stateName;
    }
    if (paymentStateLabel) {
      paymentStateLabel.textContent = stateName;
    }
    if (paymentStateCopy && copy) {
      paymentStateCopy.textContent = copy;
    }
  }

  function setEmailState(stateName, message) {
    if (!emailState) {
      return;
    }

    emailState.classList.remove('is-verified', 'is-error');
    if (stateName === 'verified') {
      emailState.classList.add('is-verified');
    } else if (stateName === 'error') {
      emailState.classList.add('is-error');
    }
    emailState.dataset.state = stateName;
    emailState.textContent = message;
  }

  function setEmailVerified(verified) {
    if (emailVerifiedFlag) {
      emailVerifiedFlag.value = verified ? '1' : '0';
    }
    state.fields = {
      ...state.fields,
      email_verified: !!verified,
    };
    updatePreviewFromForm();
    saveState();
  }

  function sendVerificationCode() {
    const email = verificationEmailInput ? verificationEmailInput.value.trim() : '';
    if (!email) {
      setEmailState('error', 'Add your email first.');
      return;
    }

    setEmailState('sending', 'Sending code...');
    fetch('/api/email-verification/send/', {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]').value,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ email }).toString(),
    })
      .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
      .then(({ ok, data }) => {
        if (!ok) {
          throw new Error(data.error || 'Could not send code.');
        }
        const suffix = data.verification_code ? ` Code: ${data.verification_code}` : '';
        setEmailState('sent', `Code sent. Check your inbox.${suffix}`);
      })
      .catch((error) => {
        setEmailState('error', error.message || 'Could not send code.');
      });
  }

  function verifyVerificationCode() {
    const email = verificationEmailInput ? verificationEmailInput.value.trim() : '';
    const code = verificationCodeInput ? verificationCodeInput.value.trim() : '';
    if (!email || !code) {
      setEmailState('error', 'Add email and code first.');
      return;
    }

    setEmailState('sending', 'Verifying code...');
    fetch('/api/email-verification/verify/', {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]').value,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ email, code }).toString(),
    })
      .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
      .then(({ ok, data }) => {
        if (!ok) {
          throw new Error(data.error || 'Verification failed.');
        }
        setEmailState('verified', data.badge || 'Verified Student');
        setEmailVerified(true);
      })
      .catch((error) => {
        setEmailVerified(false);
        setEmailState('error', error.message || 'Verification failed.');
      });
  }

  function updatePreviewFromForm() {
    const shopName = form.elements.shop_name ? form.elements.shop_name.value.trim() : '';
    const tagline = form.elements.tagline ? form.elements.tagline.value.trim() : '';
    const category = getCheckedValue('category') || 'Electronics';
    const slug = generateSlug(shopName);
    const description = form.elements.description ? form.elements.description.value.trim() : '';
    const whatsapp = form.elements.whatsapp ? form.elements.whatsapp.value.trim() : '';
    const affiliationMode = getCheckedValue('affiliation_mode_choice') || 'skip';
    const university = form.elements.university_id ? form.elements.university_id.options[form.elements.university_id.selectedIndex]?.text || '' : '';
    const location = form.elements.location_id ? form.elements.location_id.options[form.elements.location_id.selectedIndex]?.text || '' : '';
    const verified = emailVerifiedFlag ? emailVerifiedFlag.value === '1' || emailVerifiedFlag.value === 'true' : false;
    const initials = getInitials(shopName || tagline || 'Shop');

    if (slugInput) {
      slugInput.value = slug;
    }
    if (slugPreview) {
      slugPreview.textContent = slug || 'your-shop';
    }
    if (previewSlug) {
      previewSlug.textContent = slug || 'your-shop';
    }
    if (previewName) {
      previewName.textContent = shopName || 'Your shop';
    }
    if (previewShop) {
      previewShop.textContent = shopName || 'Your shop';
    }
    if (previewCategory) {
      previewCategory.textContent = category;
    }
    if (previewAffiliation) {
      previewAffiliation.textContent =
        affiliationMode === 'university' ? university || 'University' :
        affiliationMode === 'location' ? location || 'Location' :
        'Independent';
      if (verified) {
        previewAffiliation.textContent += ' · Verified';
      }
    }
    if (previewDescription) {
      previewDescription.textContent = description || 'Tell buyers what you sell and how you stand out.';
    }
    if (previewWhatsapp) {
      previewWhatsapp.textContent = whatsapp || '—';
    }
    if (previewLogoText) {
      previewLogoText.textContent = initials;
    }
    if (reviewName) {
      reviewName.textContent = shopName || '—';
    }
    if (reviewSlug) {
      reviewSlug.textContent = slug || '—';
    }
    if (reviewCategory) {
      reviewCategory.textContent = category;
    }
    if (reviewWhatsapp) {
      reviewWhatsapp.textContent = whatsapp || '—';
    }
    if (descriptionCount) {
      descriptionCount.textContent = String(description.length);
    }

    const selectedTheme = config.themes.find((theme) => theme.id === themeIdInput.value) || defaultTheme;
    if (reviewTheme) {
      reviewTheme.textContent = selectedTheme ? selectedTheme.name : '—';
    }

    state.fields = {
      ...state.fields,
      ...getFieldSnapshot(),
    };

    state.slugStatus = state.slugStatus || 'idle';
    saveState();
    validateCurrentStep();
    renderStep(state.step);
  }

  function applyFilePreview(input, target) {
    const file = input.files && input.files[0];
    if (!file || !target) {
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      target.style.backgroundImage = `url(${reader.result})`;
      target.classList.add('has-image');
      target.dataset.hasImage = 'true';
    };
    reader.readAsDataURL(file);
  }

  function checkSlugAvailability(value) {
    const slug = value || '';
    if (!slug) {
      state.slugStatus = 'idle';
      setSlugStatus('idle', 'Type a name');
      return;
    }

    const requestId = ++slugRequestId;
    state.slugStatus = 'checking';
    setSlugStatus('checking', 'Checking...');

    fetch(`/api/check-slug/?slug=${encodeURIComponent(slug)}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then((response) => response.json())
      .then((data) => {
        if (requestId !== slugRequestId) {
          return;
        }

        if (data.available) {
          state.slugStatus = 'available';
          setSlugStatus('available', 'Available');
          return;
        }

        state.slugStatus = 'taken';
        setSlugStatus('taken', data.suggestion ? `Taken · try ${data.suggestion}` : 'Taken');
      })
      .catch(() => {
        if (requestId !== slugRequestId) {
          return;
        }
        state.slugStatus = 'error';
        setSlugStatus('error', 'Could not check right now');
      });
  }

  function stopPaymentPolling() {
    if (paymentPollTimer) {
      clearInterval(paymentPollTimer);
      paymentPollTimer = null;
    }
    paymentPollDeadline = null;
  }

  function pollPaymentStatus(referenceId) {
    fetch(`/api/poll-payment/?ref=${encodeURIComponent(referenceId)}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then((response) => response.json())
      .then((data) => {
        if (!data || !data.status) {
          return;
        }

        if (data.status === 'success') {
          setPaymentState('success', 'Payment confirmed. Your shop is now active.');
          window.localStorage.removeItem(storageKey);
          stopPaymentPolling();
          return;
        }

        if (data.status === 'failed' || data.status === 'expired') {
          setPaymentState('failed', 'The payment failed or timed out. Try again.');
          stopPaymentPolling();
          return;
        }

        setPaymentState('waiting', 'Check your phone and approve the M-Pesa prompt.');
      })
      .catch(() => {
        setPaymentState('waiting', 'Waiting for payment confirmation...');
      });
  }

  function startPaymentPolling(referenceId) {
    if (!referenceId) {
      return;
    }

    stopPaymentPolling();
    paymentPollDeadline = Date.now() + 90000;
    setPaymentState('waiting', 'Check your phone and approve the M-Pesa prompt.');
    pollPaymentStatus(referenceId);
    paymentPollTimer = window.setInterval(() => {
      if (paymentPollDeadline && Date.now() > paymentPollDeadline) {
        setPaymentState('failed', 'Payment timed out. Please try again.');
        stopPaymentPolling();
        return;
      }
      pollPaymentStatus(referenceId);
    }, 3000);
  }

  function validateCurrentStep() {
    const step = state.step;
    let valid = true;

    if (step === 1) {
      const name = form.elements.shop_name ? form.elements.shop_name.value.trim() : '';
      const category = getCheckedValue('category');
      valid = name.length >= 3 && !!category && state.slugStatus !== 'taken' && state.slugStatus !== 'checking';
    } else if (step === 2) {
      const mode = getCheckedValue('affiliation_mode_choice') || 'skip';
      const university = form.elements.university_id ? form.elements.university_id.value : '';
      const location = form.elements.location_id ? form.elements.location_id.value : '';
      valid = mode === 'skip' || (mode === 'university' ? !!university : !!location);
    } else if (step === 3) {
      valid = !!themeIdInput.value;
    } else if (step === 4) {
      valid = true;
    } else if (step === 5) {
      const description = form.elements.description ? form.elements.description.value.trim() : '';
      const whatsapp = form.elements.whatsapp ? form.elements.whatsapp.value.trim() : '';
      valid = description.length >= 20 && whatsapp.length >= 8;
    } else if (step === 6) {
      const paymentPhone = paymentPhoneInput ? paymentPhoneInput.value.trim() : '';
      valid = !!(form.elements.terms && form.elements.terms.checked) && paymentPhone.length >= 8;
    }

    if (nextButton) {
      nextButton.disabled = !valid || step === 6;
    }
    if (submitButton) {
      submitButton.disabled = !valid;
    }
    return valid;
  }

  function renderStep(step) {
    state.step = step;
    if (form.elements.wizard_step) {
      form.elements.wizard_step.value = String(step);
    }

    stepPanels.forEach((panel) => {
      panel.classList.toggle('is-active', Number(panel.dataset.stepPanel) === step);
    });

    stepperItems.forEach((item) => {
      const itemStep = Number(item.dataset.stepJump);
      item.classList.toggle('is-active', itemStep === step);
      item.classList.toggle('is-complete', itemStep < step);
    });

    if (prevButton) {
      prevButton.disabled = step <= 1;
    }
    if (nextButton) {
      nextButton.classList.toggle('d-none', step >= 6);
    }
    if (submitButton) {
      submitButton.classList.toggle('d-none', step !== 6);
    }

    validateCurrentStep();
    saveState();
  }

  function syncFromState() {
    const fields = state.fields || {};

    if (form.elements.shop_name) {
      form.elements.shop_name.value = fields.shop_name || '';
    }
    if (form.elements.tagline) {
      form.elements.tagline.value = fields.tagline || '';
    }
    if (form.elements.description) {
      form.elements.description.value = fields.description || '';
    }
    if (form.elements.whatsapp) {
      form.elements.whatsapp.value = fields.whatsapp || '';
    }
    if (form.elements.location) {
      form.elements.location.value = fields.location || '';
    }
    if (form.elements.instagram) {
      form.elements.instagram.value = fields.instagram || '';
    }
    if (form.elements.tiktok) {
      form.elements.tiktok.value = fields.tiktok || '';
    }
    if (form.elements.twitter) {
      form.elements.twitter.value = fields.twitter || '';
    }
    if (form.elements.university_id) {
      form.elements.university_id.value = fields.university_id || '';
    }
    if (form.elements.location_id) {
      form.elements.location_id.value = fields.location_id || '';
    }
    if (form.elements.verification_email) {
      form.elements.verification_email.value = fields.verification_email || '';
    }
    if (form.elements.terms) {
      form.elements.terms.checked = !!fields.terms;
    }
    if (paymentPhoneInput) {
      paymentPhoneInput.value = fields.payment_phone || '';
    }

    if (fields.category) {
      form.querySelectorAll('input[name="category"]').forEach((input) => {
        input.checked = input.value === fields.category;
      });
    }

    if (fields.affiliation_mode_choice) {
      setAffiliationMode(fields.affiliation_mode_choice);
    } else {
      setAffiliationMode(state.affiliationMode || 'skip');
    }

    setTheme(state.themeId);
    setAccent(state.accentColor);
    setBannerPreset(state.bannerPreset);
    setInitialsStyle(state.initialsStyle);

    if (slugInput) {
      slugInput.value = fields.slug || generateSlug(fields.shop_name || '');
    }
    if (slugPreview) {
      slugPreview.textContent = slugInput.value || 'your-shop';
    }

    state.step = Number(shell.dataset.startStep || state.step || 1);
    setPaymentState(
      initialPaymentState,
      initialPaymentState === 'waiting'
        ? 'Check your phone and approve the M-Pesa prompt.'
        : initialPaymentState === 'success'
          ? 'Payment confirmed. Your shop is now active.'
          : initialPaymentState === 'failed'
            ? 'The payment failed or timed out. You can try again.'
            : 'Ready when you are.'
    );

    renderStep(state.step || 1);
    updatePreviewFromForm();

    if (initialPaymentState === 'waiting' && initialPaymentRef) {
      startPaymentPolling(initialPaymentRef);
    }
  }

  function bindEvents() {
    form.addEventListener('input', (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      if (target.id === 'shop-name') {
        const slug = generateSlug(target.value);
        if (slugInput) {
          slugInput.value = slug;
        }
        if (slugPreview) {
          slugPreview.textContent = slug || 'your-shop';
        }
        clearTimeout(slugTimer);
        slugTimer = window.setTimeout(() => checkSlugAvailability(slug), 400);
      }

      if (target.id === 'shop-description' && descriptionCount) {
        descriptionCount.textContent = String(target.value.length);
      }

      if (target.id === 'verification-email') {
        setEmailVerified(false);
        setEmailState('idle', 'Not verified');
      }

      state.fields = {
        ...state.fields,
        ...getFieldSnapshot(),
      };
      updatePreviewFromForm();
    });

    form.addEventListener('change', (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      if (target.matches('input[name="affiliation_mode_choice"]')) {
        setAffiliationMode(target.value);
      }

      if (target.matches('input[name="theme_choice"]')) {
        setTheme(target.value);
      }

      if (target.matches('input[name="category"]')) {
        updatePreviewFromForm();
      }

      if (target.id === 'shop-logo') {
        applyFilePreview(target, previewLogo);
      }

      if (target.id === 'shop-banner') {
        applyFilePreview(target, previewBanner || previewShell);
      }

      if (target.name === 'terms') {
        validateCurrentStep();
      }

      state.fields = {
        ...state.fields,
        ...getFieldSnapshot(),
      };
      updatePreviewFromForm();
    });

    document.querySelectorAll('[data-step-jump]').forEach((button) => {
      button.addEventListener('click', () => {
        renderStep(Number(button.dataset.stepJump));
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });

    if (prevButton) {
      prevButton.addEventListener('click', () => {
        if (state.step > 1) {
          renderStep(state.step - 1);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    }

    if (nextButton) {
      nextButton.addEventListener('click', () => {
        if (validateCurrentStep() && state.step < 6) {
          renderStep(state.step + 1);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    }

    document.querySelectorAll('[data-accent]').forEach((button) => {
      button.addEventListener('click', () => setAccent(button.dataset.accent));
    });

    document.querySelectorAll('[data-banner-preset]').forEach((button) => {
      button.addEventListener('click', () => setBannerPreset(button.dataset.bannerPreset));
    });

    document.querySelectorAll('[data-initials-style]').forEach((button) => {
      button.addEventListener('click', () => setInitialsStyle(button.dataset.initialsStyle));
    });

    if (previewToggle) {
      previewToggle.addEventListener('click', () => {
        shell.classList.toggle('is-preview-open');
      });
    }

    if (paymentRetryButton) {
      paymentRetryButton.addEventListener('click', () => {
        if (validateCurrentStep()) {
          form.requestSubmit(submitButton || form.querySelector('[type="submit"]'));
        }
      });
    }

    if (paymentChangeNumberButton) {
      paymentChangeNumberButton.addEventListener('click', () => {
        if (paymentPhoneInput) {
          paymentPhoneInput.focus();
          paymentPhoneInput.select?.();
        }
        setPaymentState('idle', 'Ready when you are.');
      });
    }

    if (emailSendButton) {
      emailSendButton.addEventListener('click', sendVerificationCode);
    }

    if (emailVerifyButton) {
      emailVerifyButton.addEventListener('click', verifyVerificationCode);
    }

    document.addEventListener('keydown', (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }

      if (event.key === 'Escape' && state.step > 1) {
        event.preventDefault();
        renderStep(state.step - 1);
        return;
      }

      if (event.key === 'Enter' && target.tagName !== 'TEXTAREA') {
        if (state.step < 6 && validateCurrentStep()) {
          event.preventDefault();
          renderStep(state.step + 1);
        }
      }
    });

    form.addEventListener('submit', (event) => {
      updatePreviewFromForm();
      if (!validateCurrentStep()) {
        event.preventDefault();
        return;
      }
      if (state.step === 6) {
        setPaymentState('sending', 'Sending the M-Pesa prompt...');
      }
    });
  }

  syncFromState();
  bindEvents();
  checkSlugAvailability(slugInput ? slugInput.value : '');
})();
