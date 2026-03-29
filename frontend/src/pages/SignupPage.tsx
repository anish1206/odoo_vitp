import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

import { useAuth } from "../context/AuthContext";

const COUNTRIES: Array<{ code: string; name: string; currency: string }> = [
  { code: "IN", name: "India", currency: "INR" },
  { code: "US", name: "United States", currency: "USD" },
  { code: "GB", name: "United Kingdom", currency: "GBP" },
  { code: "DE", name: "Germany", currency: "EUR" },
  { code: "AE", name: "United Arab Emirates", currency: "AED" },
  { code: "SG", name: "Singapore", currency: "SGD" },
  { code: "JP", name: "Japan", currency: "JPY" },
  { code: "AU", name: "Australia", currency: "AUD" },
  { code: "CA", name: "Canada", currency: "CAD" },
];

export const SignupPage = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();

  const [companyName, setCompanyName] = useState("");
  const [countryCode, setCountryCode] = useState("IN");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getApiErrorMessage = (unknownError: unknown): string => {
    if (!axios.isAxiosError(unknownError)) {
      return "Signup failed. Check details and try again.";
    }

    const detail = unknownError.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      const firstDetail = detail[0];
      if (
        firstDetail &&
        typeof firstDetail === "object" &&
        "msg" in firstDetail &&
        typeof firstDetail.msg === "string"
      ) {
        return firstDetail.msg;
      }
    }

    return "Signup failed. Check details and try again.";
  };

  const selectedCountry = useMemo(
    () => COUNTRIES.find((country) => country.code === countryCode),
    [countryCode],
  );

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    if (
      !companyName ||
      !firstName ||
      !lastName ||
      !email ||
      !password ||
      !confirmPassword
    ) {
      setError("All fields are required.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Password and confirm password must match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);
    try {
      const normalizedCompanyName = companyName.trim();
      const normalizedFirstName = firstName.trim();
      const normalizedLastName = lastName.trim();
      const normalizedEmail = email.trim().toLowerCase();

      await signup({
        company_name: normalizedCompanyName,
        country_code: countryCode,
        admin_first_name: normalizedFirstName,
        admin_last_name: normalizedLastName,
        email: normalizedEmail,
        password,
      });
      navigate("/", { replace: true });
    } catch (unknownError) {
      setError(getApiErrorMessage(unknownError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Create company admin</h1>
        <p className="muted">
          First signup creates your company and admin account together.
        </p>

        <label htmlFor="companyName">Company name</label>
        <input
          id="companyName"
          type="text"
          value={companyName}
          onChange={(event) => setCompanyName(event.target.value)}
          placeholder="Acme Corp"
        />

        <label htmlFor="country">Country</label>
        <select
          id="country"
          value={countryCode}
          onChange={(event) => setCountryCode(event.target.value)}
        >
          {COUNTRIES.map((country) => (
            <option key={country.code} value={country.code}>
              {country.name} ({country.code})
            </option>
          ))}
        </select>
        <p className="muted">Base currency: {selectedCountry?.currency ?? "-"}</p>

        <div className="split-inputs">
          <div>
            <label htmlFor="firstName">First name</label>
            <input
              id="firstName"
              type="text"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              placeholder="Anish"
            />
          </div>
          <div>
            <label htmlFor="lastName">Last name</label>
            <input
              id="lastName"
              type="text"
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
              placeholder="K"
            />
          </div>
        </div>

        <label htmlFor="signupEmail">Email</label>
        <input
          id="signupEmail"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="admin@acme.com"
        />

        <div className="split-inputs">
          <div>
            <label htmlFor="signupPassword">Password</label>
            <input
              id="signupPassword"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Min 8 characters"
            />
          </div>
          <div>
            <label htmlFor="confirmPassword">Confirm password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Repeat password"
            />
          </div>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating account..." : "Signup"}
        </button>

        <p className="muted auth-footer">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </form>
    </div>
  );
};
