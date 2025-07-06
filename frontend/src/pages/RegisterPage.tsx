import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/common/Card';

const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const { register: registerUser, isLoading, error } = useAuthStore();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data.email, data.password, data.full_name);
      navigate('/dashboard');
    } catch (error) {
      // Error is handled in the store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-primary-600 mb-2">
            Fantasy Football Assistant
          </h1>
          <p className="text-gray-600">AI-powered insights for winning leagues</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create your account</CardTitle>
            <CardDescription>
              Get started with AI-powered fantasy football insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              <Input
                label="Full name"
                type="text"
                autoComplete="name"
                error={errors.full_name?.message}
                {...register('full_name')}
              />

              <Input
                label="Email address"
                type="email"
                autoComplete="email"
                error={errors.email?.message}
                {...register('email')}
              />

              <Input
                label="Password"
                type="password"
                autoComplete="new-password"
                error={errors.password?.message}
                {...register('password')}
              />

              <Input
                label="Confirm password"
                type="password"
                autoComplete="new-password"
                error={errors.confirmPassword?.message}
                {...register('confirmPassword')}
              />

              <Button
                type="submit"
                className="w-full"
                isLoading={isLoading}
              >
                Create account
              </Button>
            </form>

            <div className="mt-6 text-center text-sm">
              <span className="text-gray-600">Already have an account? </span>
              <Link
                to="/login"
                className="font-medium text-primary-600 hover:text-primary-500"
              >
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}