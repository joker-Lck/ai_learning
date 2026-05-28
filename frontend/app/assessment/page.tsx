import { redirect } from 'next/navigation';

export default function AssessmentPage() {
  redirect('/dashboard?module=assessment');
}
