// Find the form and message areas in the HTML so JavaScript can update them.
const API_BASE_URL = "https://linkedin-post-generators.onrender.com";// Set this to the deployed Render API URL before publishing.
const postForm = document.querySelector("#post-form");
const topicInput = document.querySelector("#topic");
const purposeSelect = document.querySelector("#purpose");
const audienceInput = document.querySelector("#audience");
const toneSelect = document.querySelector("#tone");
const lengthSelect = document.querySelector("#length");
const additionalInfoInput = document.querySelector("#additional-info");
const errorMessage = document.querySelector("#error-message");
const postOutput = document.querySelector("#post-output");
const loadingMessage = document.querySelector("#loading-message");

// Listen for the form's submit event and send the entered choices to FastAPI.
postForm.addEventListener("submit", async (event) => {
  // Keep the browser from reloading the page when the form is submitted.
  event.preventDefault();

  // The browser's required-field check allows spaces, so trim the topic too.
  if (topicInput.value.trim() === "") {
    errorMessage.textContent = "Please enter a topic using at least one non-space character.";
    errorMessage.hidden = false;
    topicInput.focus();
    return;
  }

  // Put the form values into an object whose keys match the FastAPI model.
  const requestData = {
    topic: topicInput.value.trim(),
    purpose: purposeSelect.value,
    tone: toneSelect.value,
    audience: audienceInput.value.trim(),
    length: lengthSelect.value,
    additional_info: additionalInfoInput.value.trim(),
  };

  // Clear old messages and show the loading message while fetch is in progress.
  errorMessage.hidden = true;
  errorMessage.textContent = "";
  postOutput.textContent = "";
  postOutput.classList.remove("has-response");
  loadingMessage.hidden = false;

  try {
    // Send the form data to the FastAPI endpoint as a JSON POST request.
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
    });

    // Convert the JSON response body into a JavaScript object.
    const responseData = await response.json();

    // A response with a 4xx or 5xx status is not a successful request.
    if (!response.ok) {
      let details = responseData.detail;

      // FastAPI sends validation errors as a list of details.
      if (Array.isArray(details)) {
        details = details.map((item) => item.msg).join(" ");
      }

      errorMessage.textContent = `Request error (${response.status}): ${details || "The server could not process this request."}`;
      errorMessage.hidden = false;
      return;
    }

    // Show a generated post if available; otherwise show the current dummy response.
    if (responseData.post) {
      postOutput.textContent = responseData.post;
    } else {
      postOutput.textContent = [
        responseData.message,
        `Topic: ${responseData.topic}`,
        `Tone: ${responseData.tone}`,
        `Audience: ${responseData.audience}`,
        `Length: ${responseData.length}`,
      ].join("\n\n");
    }
    postOutput.classList.add("has-response");
  } catch (error) {
    // This usually means the backend is stopped or the browser blocked the request.
    errorMessage.textContent =
      `Could not reach the backend at ${API_BASE_URL}. Check the API URL and that the backend is running.`;
    errorMessage.hidden = false;
  } finally {
    // Always hide the loading message after success or failure.
    loadingMessage.hidden = true;
  }
});
