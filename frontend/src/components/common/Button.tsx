/**
 * Button.tsx - 재사용 가능한 버튼 컴포넌트
 * 
 * 📊 Data Sources:
 *   - Props: variant, size, children, onClick, disabled, etc.
 * 
 * 🔗 Dependencies:
 *   - react: ButtonHTMLAttributes
 *   - Tailwind CSS: 색상 및 크기 스타일
 * 
 * 📤 Props:
 *   - variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
 *   - size?: 'sm' | 'md' | 'lg'
 *   - children: ReactNode
 *   - onClick?: () => void
 *   - disabled?: boolean
 *   - ...props: 기타 button 속성
 * 
 * 🔄 Used By:
 *   - 모든 페이지 (폼, 액션 버튼)
 *   - Modal 컴포넌트
 *   - Dashboard, Portfolio, Settings 등
 * 
 * 📝 Notes:
 *   - 4가지 variant (primary, secondary, danger, ghost)
 *   - 3가지 size (sm, md, lg)
 *   - hover/disabled 상태 스타일 포함
 */

import React from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  onClick,
  children,
  disabled = false,
  className = '',
  type = 'button',
}) => {
  const baseStyles = 'font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';

  const variantStyles = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800 focus:ring-gray-500',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
    success: 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-500',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      type={type}
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''
        } ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
