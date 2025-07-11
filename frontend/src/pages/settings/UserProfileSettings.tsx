import { useState, useEffect } from 'react';
import { useAuthStore } from '../../store/useAuthStore';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Camera, Loader2, AlertCircle, CheckCircle, Trash2 } from 'lucide-react';
import api from '../../services/api';

interface ProfileData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  bio: string;
  avatar_url: string | null;
}

export function UserProfileSettings() {
  const { user, updateUser } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [profile, setProfile] = useState<ProfileData>({
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    bio: user?.bio || '',
    avatar_url: user?.avatar_url || null,
  });

  useEffect(() => {
    if (user) {
      setProfile({
        username: user.username || '',
        email: user.email || '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        bio: user.bio || '',
        avatar_url: user.avatar_url || null,
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.put('/user/profile', {
        username: profile.username,
        first_name: profile.first_name,
        last_name: profile.last_name,
        bio: profile.bio,
      });
      
      updateUser(response.data);
      setSuccess('Profile updated successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/user/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setProfile(prev => ({ ...prev, avatar_url: response.data.avatar_url }));
      updateUser({ ...user, avatar_url: response.data.avatar_url });
      setSuccess('Avatar uploaded successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload avatar');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAvatar = async () => {
    if (!confirm('Are you sure you want to delete your avatar?')) return;

    setLoading(true);
    setError(null);

    try {
      await api.delete('/user/avatar');
      setProfile(prev => ({ ...prev, avatar_url: null }));
      updateUser({ ...user, avatar_url: null });
      setSuccess('Avatar deleted successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete avatar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="border-b pb-4 mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Profile Information</h2>
        <p className="mt-1 text-sm text-gray-600">
          Update your account profile and personal information
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6 bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Avatar Section */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-4">
          Profile Picture
        </label>
        <div className="flex items-center space-x-6">
          <div className="relative">
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt="Profile"
                className="h-24 w-24 rounded-full object-cover"
              />
            ) : (
              <div className="h-24 w-24 rounded-full bg-gray-200 flex items-center justify-center">
                <span className="text-2xl font-medium text-gray-600">
                  {profile.first_name?.charAt(0) || profile.username?.charAt(0) || '?'}
                </span>
              </div>
            )}
            {uploading && (
              <div className="absolute inset-0 rounded-full bg-black bg-opacity-50 flex items-center justify-center">
                <Loader2 className="h-6 w-6 text-white animate-spin" />
              </div>
            )}
          </div>
          <div className="space-x-3">
            <label className="relative cursor-pointer">
              <input
                type="file"
                className="sr-only"
                accept="image/*"
                onChange={handleAvatarUpload}
                disabled={uploading}
              />
              <Button variant="outline" disabled={uploading}>
                <Camera className="h-4 w-4 mr-2" />
                Change Photo
              </Button>
            </label>
            {profile.avatar_url && (
              <Button 
                variant="outline" 
                onClick={handleDeleteAvatar}
                disabled={loading}
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
        <p className="mt-2 text-xs text-gray-500">
          Recommended: Square image, at least 200x200px, max 5MB
        </p>
      </div>

      {/* Profile Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <Input
              type="text"
              value={profile.username}
              onChange={(e) => setProfile({ ...profile, username: e.target.value })}
              disabled={loading}
              required
              minLength={3}
              maxLength={50}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <Input
              type="email"
              value={profile.email}
              disabled
              className="bg-gray-50"
            />
            <p className="mt-1 text-xs text-gray-500">
              Email cannot be changed
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              First Name
            </label>
            <Input
              type="text"
              value={profile.first_name}
              onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
              disabled={loading}
              maxLength={100}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Last Name
            </label>
            <Input
              type="text"
              value={profile.last_name}
              onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
              disabled={loading}
              maxLength={100}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Bio
          </label>
          <textarea
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            rows={4}
            value={profile.bio}
            onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
            disabled={loading}
            maxLength={500}
            placeholder="Tell us a bit about yourself..."
          />
          <p className="mt-1 text-xs text-gray-500">
            {profile.bio.length}/500 characters
          </p>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}