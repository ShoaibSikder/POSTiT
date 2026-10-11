const allowedImageTypes = new Set(["image/jpeg", "image/png", "image/webp"]);

export function validateImageFiles(
  files,
  { maxFiles = 5, maxBytes = 5 * 1024 * 1024 } = {},
) {
  const selected = Array.from(files || []);
  if (selected.length > maxFiles) {
    return `Choose no more than ${maxFiles} images.`;
  }
  const invalidType = selected.find((file) => !allowedImageTypes.has(file.type));
  if (invalidType) return "Use JPEG, PNG, or WebP images.";
  const tooLarge = selected.find((file) => file.size > maxBytes);
  if (tooLarge) return "Each image must be 5 MB or smaller.";
  return "";
}

export function validateRequired(value, label) {
  return String(value || "").trim() ? "" : `${label} is required.`;
}

export function validatePasswordMatch(password, confirmation) {
  return password === confirmation ? "" : "The passwords do not match.";
}