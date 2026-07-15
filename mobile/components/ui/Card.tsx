import React from 'react';
import { View, Text } from 'react-native';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  headerRight?: React.ReactNode;
}

export function Card({ children, title, subtitle, className = '', headerRight }: CardProps) {
  return (
    <View className={`bg-primary-light rounded-xl border border-border p-4 ${className}`}>
      {(title || headerRight) && (
        <View className="flex-row items-center justify-between mb-3">
          <View className="flex-1">
            {title && (
              <Text className="text-text-primary text-lg font-bold">{title}</Text>
            )}
            {subtitle && (
              <Text className="text-text-secondary text-sm mt-1">{subtitle}</Text>
            )}
          </View>
          {headerRight}
        </View>
      )}
      {children}
    </View>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
}

export function StatCard({ label, value, icon, color = '#64ffda' }: StatCardProps) {
  return (
    <View className="bg-primary-light rounded-xl border border-border p-4 flex-1">
      <View className="flex-row items-center gap-2 mb-2">
        {icon}
        <Text className="text-text-secondary text-xs">{label}</Text>
      </View>
      <Text className="text-2xl font-bold" style={{ color }}>
        {value}
      </Text>
    </View>
  );
}
