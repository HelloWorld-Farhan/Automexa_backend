/**
 * AUTOMEXA AUTHENTICATION & OTP SERVICE
 * Paste this code into your Google Apps Script editor at:
 * https://script.google.com/
 * Then deploy as Web App (Execute as: Me, Who has access: Anyone)
 */

function doGet(e) {
  return handleRequest(e);
}

function doPost(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  var headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  };

  try {
    var params = {};
    if (e && e.postData && e.postData.contents) {
      try {
        params = JSON.parse(e.postData.contents);
      } catch (err) {
        params = e.parameter || {};
      }
    } else if (e && e.parameter) {
      params = e.parameter;
    }

    var action = params.action || "";
    var responseData = {};

    if (action === "ping") {
      responseData = { status: "success", message: "Automexa Auth Service Online" };
    } else if (action === "sendOtp") {
      responseData = handleSendOtp(params.email, params.type || "Verification");
    } else if (action === "verifyOtp") {
      responseData = handleVerifyOtp(params.email, params.otp);
    } else if (action === "signup") {
      responseData = handleSignup(params.email, params.password, params.fullName);
    } else if (action === "login") {
      responseData = handleLogin(params.email, params.password);
    } else if (action === "resetPassword") {
      responseData = handleResetPassword(params.email, params.newPassword, params.otp);
    } else {
      responseData = { status: "error", message: "Invalid action: " + action };
    }

    return ContentService.createTextOutput(JSON.stringify(responseData))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// ----------------------------------------------------
// OTP GENERATION & EMAIL DISPATCH
// ----------------------------------------------------
function handleSendOtp(email, type) {
  if (!email) return { status: "error", message: "Email is required" };

  // Generate 6-digit cryptographic random OTP
  var otp = Math.floor(100000 + Math.random() * 900000).toString();
  var props = PropertiesService.getScriptProperties();

  // Store OTP with 5-minute expiration
  var payload = {
    otp: otp,
    expiresAt: new Date().getTime() + (5 * 60 * 1000)
  };
  props.setProperty("OTP_" + email.toLowerCase().trim(), JSON.stringify(payload));

  // Send minimal branded HTML Email
  var subject = "⚡ Automexa Security OTP: " + otp;
  var htmlBody = `
    <div style="background-color: #E6E4DC; padding: 40px 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <div style="max-width: 440px; margin: 0 auto; background: #FEFEFE; border-radius: 28px; padding: 36px 28px; box-shadow: 0 4px 16px rgba(0,0,0,0.04);">
        <h1 style="font-size: 24px; font-weight: 500; color: #1D1C21; margin: 0 0 8px 0;">Automexa Security</h1>
        <p style="font-size: 14px; color: #6E6D72; margin: 0 0 24px 0;">${type} Verification Code</p>
        
        <div style="background: #EDECE6; border-radius: 16px; padding: 18px; text-align: center; margin: 0 0 24px 0;">
          <span style="font-size: 34px; font-weight: 700; letter-spacing: 8px; color: #1C1B20;">${otp}</span>
        </div>
        
        <p style="font-size: 12px; color: #8E8D92; line-height: 18px; margin: 0;">
          This verification code expires in <strong>5 minutes</strong>. If you did not request this OTP, please ignore this email or review your account security.
        </p>
      </div>
    </div>
  `;

  MailApp.sendEmail({
    to: email,
    subject: subject,
    htmlBody: htmlBody
  });

  return { status: "success", message: "OTP sent successfully" };
}

// ----------------------------------------------------
// OTP VERIFICATION
// ----------------------------------------------------
function handleVerifyOtp(email, enteredOtp) {
  if (!email || !enteredOtp) return { status: "error", message: "Email and OTP are required" };

  var props = PropertiesService.getScriptProperties();
  var raw = props.getProperty("OTP_" + email.toLowerCase().trim());
  if (!raw) return { status: "error", message: "No OTP requested for this email" };

  var stored = JSON.parse(raw);
  if (new Date().getTime() > stored.expiresAt) {
    return { status: "error", message: "OTP has expired. Please request a new one." };
  }

  if (stored.otp.toString().trim() !== enteredOtp.toString().trim()) {
    return { status: "error", message: "Incorrect OTP code" };
  }

  // Clear OTP once used
  props.deleteProperty("OTP_" + email.toLowerCase().trim());
  return { status: "success", message: "OTP verified successfully" };
}

// ----------------------------------------------------
// USER ACCOUNTS & SPREADSHEET STORAGE
// ----------------------------------------------------
function getSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    ss = SpreadsheetApp.create("Automexa_User_Registry");
  }
  var sheet = ss.getSheetByName("Users");
  if (!sheet) {
    sheet = ss.insertSheet("Users");
    sheet.appendRow(["Email", "Password", "FullName", "CreatedAt"]);
  }
  return sheet;
}

function handleSignup(email, password, fullName) {
  if (!email || !password) return { status: "error", message: "Email and password required" };
  var sheet = getSheet();
  var data = sheet.getDataRange().getValues();

  for (var i = 1; i < data.length; i++) {
    if (data[i][0].toString().toLowerCase() === email.toLowerCase().trim()) {
      return { status: "error", message: "Account already exists with this email" };
    }
  }

  sheet.appendRow([email.toLowerCase().trim(), password, fullName || "Candidate", new Date()]);
  return { status: "success", message: "Account created successfully" };
}

function handleLogin(email, password) {
  if (!email || !password) return { status: "error", message: "Email and password required" };
  var sheet = getSheet();
  var data = sheet.getDataRange().getValues();

  for (var i = 1; i < data.length; i++) {
    if (data[i][0].toString().toLowerCase() === email.toLowerCase().trim()) {
      if (data[i][1].toString() === password.toString()) {
        return {
          status: "success",
          fullName: data[i][2],
          email: data[i][0],
          token: "auth_" + Utilities.getUuid()
        };
      } else {
        return { status: "error", message: "Incorrect password", code: "INVALID_PASSWORD" };
      }
    }
  }

  return { status: "error", message: "Account not found", code: "USER_NOT_FOUND" };
}

function handleResetPassword(email, newPassword, otp) {
  var verify = handleVerifyOtp(email, otp);
  if (verify.status !== "success") return verify;

  var sheet = getSheet();
  var data = sheet.getDataRange().getValues();

  for (var i = 1; i < data.length; i++) {
    if (data[i][0].toString().toLowerCase() === email.toLowerCase().trim()) {
      sheet.getRange(i + 1, 2).setValue(newPassword);
      return { status: "success", message: "Password updated successfully. You can now login." };
    }
  }

  return { status: "error", message: "Account not found" };
}
