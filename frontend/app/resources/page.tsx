import { redirect } from 'next/navigation';

export default function ResourcesPage() {
  redirect('/dashboard?module=resources');
}
