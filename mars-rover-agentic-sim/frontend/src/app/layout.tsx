import "./globals.css";

import type { Metadata } from "next";
import { Space_Grotesk, Space_Mono } from "next/font/google";

const spaceGrotesk = Space_Grotesk({
	subsets: ["latin"],
	display: "swap",
	variable: "--font-sans",
});

const spaceMono = Space_Mono({
	subsets: ["latin"],
	weight: ["400", "700"],
	display: "swap",
	variable: "--font-mono",
});

export const metadata: Metadata = {
	title: "Mars Rover LangGraph Demo",
	description: "Mission-control dashboard for LangGraph rover agent scenarios.",
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en" className={`${spaceGrotesk.variable} ${spaceMono.variable}`}>
			<body className="font-sans antialiased">
				<div className="relative z-10 min-h-screen">{children}</div>
			</body>
		</html>
	);
}
