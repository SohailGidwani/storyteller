import CreateForm from '@/components/Onboarding/CreateForm'
import Link from 'next/link'

export default function CreatePage() {
  return (
    <main className="min-h-screen bg-cream">
      <div className="flex items-center gap-4 px-8 pt-10 pb-2">
        <Link
          href="/"
          className="w-11 h-11 flex items-center justify-center text-ink/50 hover:text-ink text-xl"
          aria-label="Back"
        >
          ←
        </Link>
        <h1 className="font-lora text-sienna text-4xl">Make Your Story</h1>
      </div>
      <CreateForm />
    </main>
  )
}
