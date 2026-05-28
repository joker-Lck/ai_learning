import { redirect } from 'next/navigation';

export default function LearningPathPage() {
  redirect('/dashboard?module=path');
}
