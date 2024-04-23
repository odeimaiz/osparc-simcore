/* eslint-disable no-undef */
const { test, expect } = require('@playwright/test');

import products from '../products.json';

const expectedCreateAccountLabel = {
  "osparc": "Create Account",
  "s4l": "Request Account",
  "s4lacad": "Request Account",
  "s4llite": "Request Account",
  "tis": "Request Account"
};

for (const product in products) {
  test(`Invitation required ${product}`, async ({ page }) => {
    const expectedLabel = expectedCreateAccountLabel[product];
    expect(expectedLabel).toBeTruthy();
    if (expectedLabel) {
      await page.goto(products[product]);

      const button = page.getByTestId("loginCreateAccountBtn");
      await expect(button).toBeVisible();
      await expect(button).toContainText(expectedLabel);
    }
  });
}
