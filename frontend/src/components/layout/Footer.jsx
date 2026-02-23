export default function Footer() {
  return (
    <footer className="mt-auto border-t border-[#2a2a38] bg-[#0a0a0f]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 text-center">
        <p className="text-xs text-[#55556a]">
          &copy; {new Date().getFullYear()} CinemaHub. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
