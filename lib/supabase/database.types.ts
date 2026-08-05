export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  graphql_public: {
    Tables: {
      [_ in never]: never
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      graphql: {
        Args: {
          extensions?: Json
          operationName?: string
          query?: string
          variables?: Json
        }
        Returns: Json
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
  public: {
    Tables: {
      badges: {
        Row: {
          code: string
          created_at: string
          id: number
          image_url: string | null
          name: string
          probability_weight: number
        }
        Insert: {
          code: string
          created_at?: string
          id?: never
          image_url?: string | null
          name: string
          probability_weight: number
        }
        Update: {
          code?: string
          created_at?: string
          id?: never
          image_url?: string | null
          name?: string
          probability_weight?: number
        }
        Relationships: []
      }
      departments: {
        Row: {
          code: string
          created_at: string
          id: number
          name: string
          parent_id: number | null
        }
        Insert: {
          code: string
          created_at?: string
          id?: never
          name: string
          parent_id?: number | null
        }
        Update: {
          code?: string
          created_at?: string
          id?: never
          name?: string
          parent_id?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "departments_parent_id_fkey"
            columns: ["parent_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["id"]
          },
        ]
      }
      hashtags: {
        Row: {
          created_at: string
          id: number
          name: string
          sort_order: number
        }
        Insert: {
          created_at?: string
          id?: never
          name: string
          sort_order?: number
        }
        Update: {
          created_at?: string
          id?: never
          name?: string
          sort_order?: number
        }
        Relationships: []
      }
      hearts: {
        Row: {
          created_at: string
          id: number
          is_special_day_bonus: boolean
          kudos_id: number
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: never
          is_special_day_bonus?: boolean
          kudos_id: number
          user_id: string
        }
        Update: {
          created_at?: string
          id?: never
          is_special_day_bonus?: boolean
          kudos_id?: number
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "hearts_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "kudos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "hearts_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "my_sent_kudos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "hearts_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "public_kudos_feed"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "hearts_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      kudos: {
        Row: {
          body: string
          created_at: string
          heart_count: number
          id: number
          is_anonymous: boolean
          recipient_id: string
          sender_id: string
          status: string
        }
        Insert: {
          body: string
          created_at?: string
          heart_count?: number
          id?: never
          is_anonymous?: boolean
          recipient_id: string
          sender_id: string
          status?: string
        }
        Update: {
          body?: string
          created_at?: string
          heart_count?: number
          id?: never
          is_anonymous?: boolean
          recipient_id?: string
          sender_id?: string
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "kudos_recipient_id_fkey"
            columns: ["recipient_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_sender_id_fkey"
            columns: ["sender_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      kudos_hashtags: {
        Row: {
          hashtag_id: number
          kudos_id: number
        }
        Insert: {
          hashtag_id: number
          kudos_id: number
        }
        Update: {
          hashtag_id?: number
          kudos_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "kudos_hashtags_hashtag_id_fkey"
            columns: ["hashtag_id"]
            isOneToOne: false
            referencedRelation: "hashtags"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_hashtags_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "kudos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_hashtags_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "my_sent_kudos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_hashtags_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "public_kudos_feed"
            referencedColumns: ["id"]
          },
        ]
      }
      kudos_images: {
        Row: {
          created_at: string
          id: number
          kudos_id: number
          position: number
          url: string
        }
        Insert: {
          created_at?: string
          id?: never
          kudos_id: number
          position: number
          url: string
        }
        Update: {
          created_at?: string
          id?: never
          kudos_id?: number
          position?: number
          url?: string
        }
        Relationships: [
          {
            foreignKeyName: "kudos_images_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "kudos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_images_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "my_sent_kudos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_images_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "public_kudos_feed"
            referencedColumns: ["id"]
          },
        ]
      }
      profile_badges: {
        Row: {
          awarded_at: string
          badge_id: number
          profile_id: string
        }
        Insert: {
          awarded_at?: string
          badge_id: number
          profile_id: string
        }
        Update: {
          awarded_at?: string
          badge_id?: number
          profile_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "profile_badges_badge_id_fkey"
            columns: ["badge_id"]
            isOneToOne: false
            referencedRelation: "badges"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "profile_badges_profile_id_fkey"
            columns: ["profile_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          avatar_url: string | null
          created_at: string
          department_id: number | null
          full_name: string
          id: string
          received_hearts_count: number
          received_kudos_count: number
          sent_kudos_count: number
        }
        Insert: {
          avatar_url?: string | null
          created_at?: string
          department_id?: number | null
          full_name: string
          id: string
          received_hearts_count?: number
          received_kudos_count?: number
          sent_kudos_count?: number
        }
        Update: {
          avatar_url?: string | null
          created_at?: string
          department_id?: number | null
          full_name?: string
          id?: string
          received_hearts_count?: number
          received_kudos_count?: number
          sent_kudos_count?: number
        }
        Relationships: [
          {
            foreignKeyName: "profiles_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["id"]
          },
        ]
      }
      secret_box_grants: {
        Row: {
          badge_id: number | null
          created_at: string
          id: number
          opened_at: string | null
          profile_id: string
          status: string
        }
        Insert: {
          badge_id?: number | null
          created_at?: string
          id?: never
          opened_at?: string | null
          profile_id: string
          status?: string
        }
        Update: {
          badge_id?: number | null
          created_at?: string
          id?: never
          opened_at?: string | null
          profile_id?: string
          status?: string
        }
        Relationships: [
          {
            foreignKeyName: "secret_box_grants_badge_id_fkey"
            columns: ["badge_id"]
            isOneToOne: false
            referencedRelation: "badges"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "secret_box_grants_profile_id_fkey"
            columns: ["profile_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      special_days: {
        Row: {
          created_at: string
          day: string
          id: number
          note: string | null
        }
        Insert: {
          created_at?: string
          day: string
          id?: never
          note?: string | null
        }
        Update: {
          created_at?: string
          day?: string
          id?: never
          note?: string | null
        }
        Relationships: []
      }
      user_roles: {
        Row: {
          created_at: string
          role: string
          user_id: string
        }
        Insert: {
          created_at?: string
          role: string
          user_id: string
        }
        Update: {
          created_at?: string
          role?: string
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      my_sent_kudos: {
        Row: {
          body: string | null
          created_at: string | null
          heart_count: number | null
          id: number | null
          is_anonymous: boolean | null
          recipient_avatar_url: string | null
          recipient_full_name: string | null
          recipient_id: string | null
          status: string | null
        }
        Relationships: [
          {
            foreignKeyName: "kudos_recipient_id_fkey"
            columns: ["recipient_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      public_kudos_feed: {
        Row: {
          body: string | null
          created_at: string | null
          heart_count: number | null
          id: number | null
          is_anonymous: boolean | null
          recipient_avatar_url: string | null
          recipient_full_name: string | null
          recipient_id: string | null
          sender_avatar_url: string | null
          sender_department_id: number | null
          sender_full_name: string | null
          sender_id: string | null
          status: string | null
        }
        Relationships: [
          {
            foreignKeyName: "kudos_recipient_id_fkey"
            columns: ["recipient_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Functions: {
      admin_grant_secret_box: {
        Args: { p_count: number; p_profile_ids: string[] }
        Returns: undefined
      }
      is_admin: { Args: never; Returns: boolean }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  graphql_public: {
    Enums: {},
  },
  public: {
    Enums: {},
  },
} as const

