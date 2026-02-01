import { test, expect } from '@playwright/test';

test.describe('Recruiter AI Platform E2E', () => {
  test('should complete full query workflow', async ({ page }) => {
    // Listen for console messages
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));

    // Listen for page errors
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

    // Navigate to frontend
    await page.goto('http://localhost:3000');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check what's actually loaded
    const title = await page.title();
    console.log('Page title:', title);

    // Check if we're on login page or already authenticated
    const pageContent = await page.textContent('body');
    console.log('Page content length:', pageContent.length);

    if (pageContent.includes('Sign in to Recruiter AI')) {
      // We're on login page - proceed with login
      console.log('On login page, proceeding with authentication');

      // Enable recruiter ID mode
      await page.locator('#useRecruiterId').check();

      // Enter recruiter ID
      await page.locator('#recruiterId').fill('2');

      // Submit login
      await page.locator('button[type="submit"]').click();

      // Wait for either navigation or page content change
      try {
        await page.waitForURL('**/', { timeout: 5000 });
      } catch (e) {
        // Check if we're still on login page or got redirected
        const currentUrl = page.url();
        console.log('Current URL after login:', currentUrl);
        if (currentUrl.includes('/login')) {
          throw new Error('Login failed - still on login page');
        }
      }
    } else if (pageContent.includes('Run AI Agent')) {
      // Already authenticated
      console.log('Already authenticated, on dashboard');
    } else {
      // Unexpected page
      console.log('Unexpected page content:', pageContent.substring(0, 500));
      throw new Error('Unexpected page state');
    }

    // Should be on dashboard
    await expect(page.locator('body')).toContainText('Run AI Agent');

    // Navigate to run-agent page if not already there
    if (!page.url().includes('/run-agent')) {
      await page.goto('http://localhost:3000/run-agent');
    }

    // Fill query form
    await page.locator('#query').fill('Find AI engineers in Bangalore with 2+ years experience');

    // Submit query
    await page.locator('button[type="submit"]').click();

    // Should show processing status
    await expect(page.locator('body')).toContainText('processing');

    // Wait for completion (max 30 seconds)
    await page.waitForFunction(() => {
      return document.body.textContent?.includes('completed') ||
             document.body.textContent?.includes('Top Leads Found');
    }, { timeout: 30000 });

    // Should show results or completion status
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toMatch(/(completed|Top Leads Found|leads found)/);

    console.log('Test completed successfully!');
  });
});