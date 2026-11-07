import { useState, type FormEvent } from "react";
import {
	Navigate,
	useLocation,
	useNavigate,
	type Location,
} from "react-router";
import { isApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { PageSpinner } from "../components/States";
import { TextInput } from "../components/TextInput";
import { DEFAULT_PATH } from "./tabs";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function redirectTarget(state: unknown): string {
	const from = (state as { from?: Location } | null)?.from;
	if (!from || from.pathname === "/login") return DEFAULT_PATH;
	return `${from.pathname}${from.search}${from.hash}`;
}

export function LoginPage() {
	const { user, isLoading, login } = useAuth();
	const location = useLocation();
	const navigate = useNavigate();
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [fieldErrors, setFieldErrors] = useState<{
		email?: string;
		password?: string;
	}>({});
	const [formError, setFormError] = useState<string | null>(null);
	const [submitting, setSubmitting] = useState(false);

	if (isLoading) return <PageSpinner label="Checking your session" />;
	if (user && !submitting)
		return <Navigate to={redirectTarget(location.state)} replace />;

	const onSubmit = async (event: FormEvent) => {
		event.preventDefault();
		const errors: typeof fieldErrors = {};
		if (!EMAIL_RE.test(email.trim()))
			errors.email = "Enter a valid email address.";
		if (!password) errors.password = "Enter your password.";
		setFieldErrors(errors);
		setFormError(null);
		if (errors.email || errors.password) return;

		setSubmitting(true);
		try {
			await login(email.trim(), password);
			navigate(redirectTarget(location.state), { replace: true });
		} catch (error) {
			if (isApiError(error, 401)) setFormError("Invalid email or password.");
			else if (isApiError(error)) setFormError(error.message);
			else setFormError("Something went wrong. Please try again.");
			setSubmitting(false);
		}
	};

	return (
		<main className="flex min-h-screen items-center justify-center bg-stone-50 px-4">
			<div className="w-full max-w-sm rounded-2xl border border-stone-200 bg-white p-8 shadow-sm max-md:p-6">
				<p className="font-cjk text-3xl font-bold text-red-800" lang="zh-Hans">
					ZZ
				</p>
				<h1 className="mt-2 text-xl font-semibold text-stone-900">Log in</h1>
				<p className="mt-1 text-sm text-stone-500">
					Use the account created for you.
				</p>

				<form
					noValidate
					onSubmit={onSubmit}
					className="mt-6 flex flex-col gap-4"
				>
					<TextInput
						label="Email"
						type="email"
						autoComplete="email"
						autoFocus
						value={email}
						onChange={(e) => setEmail(e.target.value)}
						error={fieldErrors.email}
					/>
					<TextInput
						label="Password"
						type="password"
						autoComplete="current-password"
						value={password}
						onChange={(e) => setPassword(e.target.value)}
						error={fieldErrors.password}
					/>
					{formError && (
						<p
							role="alert"
							className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800"
						>
							{formError}
						</p>
					)}
					<Button type="submit" pending={submitting} className="mt-2 w-full">
						{submitting ? "Logging in" : "Log in"}
					</Button>
				</form>
			</div>
		</main>
	);
}
