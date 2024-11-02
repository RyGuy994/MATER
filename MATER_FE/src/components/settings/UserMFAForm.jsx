import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";

const UserMFAForm = ({ baseurl }) => {
  const [mfaMethods, setMfaMethods] = useState([]);
  const [newMfaMethod, setNewMfaMethod] = useState({ mfa_method: "", mfa_value: "", set_primary: false });
  const [otpCode, setOtpCode] = useState("");
  const jwtToken = localStorage.getItem('jwt');

  useEffect(() => {
    fetchMfaMethods();
  }, []);

  const fetchMfaMethods = async () => {
    try {
      const response = await fetch(`${baseurl}/mfa/methods`, {
        method: "GET",
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      if (response.ok) {
        setMfaMethods(data.mfa_methods || []);
      } else {
        toast.error(data.error || "Failed to fetch MFA methods");
      }
    } catch (error) {
      console.error("Error fetching MFA methods:", error);
      toast.error("An error occurred while fetching MFA methods");
    }
  };

  const addMfaMethod = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${baseurl}/mfa/setup`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newMfaMethod),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success(data.message || "MFA method added successfully");
        fetchMfaMethods();
        setNewMfaMethod({ mfa_method: "", mfa_value: "", set_primary: false });
      } else {
        toast.error(data.error || "Failed to add MFA method");
      }
    } catch (error) {
      console.error("Error adding MFA method:", error);
      toast.error("An error occurred while adding the MFA method");
    }
  };

  const testMfaMethod = async (email) => {
    try {
      const response = await fetch(`${baseurl}/mfa/send-test-email`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success(data.message || "Test email sent successfully");
      } else {
        toast.error(data.message || "Failed to send test email");
      }
    } catch (error) {
      console.error("Error sending test email:", error);
      toast.error("An error occurred while sending the test email");
    }
  };

  // New function to verify the OTP
  const verifyOtp = async () => {
    try {
      const response = await fetch(`${baseurl}/mfa/verify-otp`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ otp_code: otpCode }),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success(data.message || "OTP verified successfully");
        setOtpCode(""); // Clear the input after successful verification
      } else {
        toast.error(data.message || "Failed to verify OTP");
      }
    } catch (error) {
      console.error("Error verifying OTP:", error);
      toast.error("An error occurred while verifying the OTP");
    }
  };

  // Handle enabling an MFA method
  const enableMfaMethod = async (method) => {
    try {
      const response = await fetch(`${baseurl}/mfa/enable`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mfa_method: method }),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success(data.message || "MFA method enabled successfully");
        fetchMfaMethods();
      } else {
        toast.error(data.error || "Failed to enable MFA method");
      }
    } catch (error) {
      console.error("Error enabling MFA method:", error);
      toast.error("An error occurred while enabling the MFA method");
    }
  };

  // Handle setting an MFA method as primary
  const setPrimaryMethod = async (method) => {
    try {
      const response = await fetch(`${baseurl}/mfa/set-primary`, {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mfa_method: method }),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success(data.message || "MFA method set as primary");
        fetchMfaMethods();
      } else {
        toast.error(data.error || "Failed to set as primary");
      }
    } catch (error) {
      console.error("Error setting primary MFA method:", error);
      toast.error("An error occurred while setting the primary method");
    }
  };

  // Handle deleting an MFA method
  const deleteMfaMethod = async (method) => {
    try {
      const response = await fetch(`${baseurl}/mfa/delete`, {
        method: "DELETE",
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mfa_method: method }),
      });
      const data = await response.json();
      if (response.ok) {
        toast.success(data.message || "MFA method deleted successfully");
        fetchMfaMethods();
      } else {
        toast.error(data.error || "Failed to delete MFA method");
      }
    } catch (error) {
      console.error("Error deleting MFA method:", error);
      toast.error("An error occurred while deleting the MFA method");
    }
  };

  return (
    <div className="mfa-management">
      <h2>MFA Management</h2>
      <form onSubmit={addMfaMethod}>
        <label>
          MFA Method:
          <select
            value={newMfaMethod.mfa_method}
            onChange={(e) => setNewMfaMethod({ ...newMfaMethod, mfa_method: e.target.value })}
            required
          >
            <option value="">Select a method</option>
            <option value="totp">TOTP - development</option>
            <option value="email">Email</option>
            <option value="sms">SMS - development</option>
          </select>
        </label>
        {(newMfaMethod.mfa_method === "email" || newMfaMethod.mfa_method === "sms") && (
          <label>
            {newMfaMethod.mfa_method.toUpperCase()} Address:
            <input
              type="text"
              value={newMfaMethod.mfa_value}
              onChange={(e) => setNewMfaMethod({ ...newMfaMethod, mfa_value: e.target.value })}
              required
            />
          </label>
        )}
        <br />
        <label>
          Set as Primary:
          <input
            type="checkbox"
            checked={newMfaMethod.set_primary}
            onChange={(e) => setNewMfaMethod({ ...newMfaMethod, set_primary: e.target.checked })}
          />
        </label>
        <br />
        <button className="standard-btn" type="submit">Add MFA Method</button>
      </form>

      <h3>Current MFA Methods</h3>
      {mfaMethods.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>MFA Method</th>
              <th>Value</th>
              <th>Primary</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {mfaMethods.map((method) => (
              <tr key={method.id}>
                <td>{method.mfa_method.toUpperCase()}</td>
                <td>{method.mfa_value || "N/A"}</td>
                <td>{method.is_primary ? "Yes" : "No"}</td>
                <td>
                  <button className="standard-btn" onClick={() => setPrimaryMethod(method.mfa_method)}>Set as Primary</button>
                  <button className="standard-btn" onClick={() => enableMfaMethod(method.mfa_method)}>Enable</button>
                  <button className="standard-del-btn" onClick={() => deleteMfaMethod(method.mfa_method)}>Delete</button>
                  {method.mfa_method === "email" && (
                    <button className="standard-btn" onClick={() => testMfaMethod(method.mfa_value)}>Test Email</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No MFA methods set up yet.</p>
      )}

      <h3>Verify OTP</h3>
      <label>
        Enter OTP:
        <input
          type="text"
          value={otpCode}
          onChange={(e) => setOtpCode(e.target.value)}
          placeholder="Enter your OTP code"
        />
      </label>
      <br />
      <button className="standard-btn" onClick={verifyOtp}>Verify OTP</button>
    </div>
  );
};

export default UserMFAForm;
