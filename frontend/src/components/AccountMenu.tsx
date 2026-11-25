import { UserButton } from '@clerk/react'
import { Settings } from 'lucide-react'

/**
 * The signed-in account and session manager powered by Clerk.
 *
 * Prominently displays the user's identity and avatar in the header.
 * Provides multi-user account switching, account profile management,
 * and quick links to settings and sign out.
 */
export function AccountMenu() {
  return (
    <div className="flex items-center gap-2 font-mono text-xs">
      <UserButton
        showName
        appearance={{
          elements: {
            userButtonAvatarBox: 'size-7',
            userButtonOuterIdentifier: 'font-medium text-foreground text-xs',
          },
        }}
      >
        <UserButton.MenuItems>
          <UserButton.Link
            label="Settings"
            labelIcon={<Settings className="size-4" />}
            href="/settings"
          />
        </UserButton.MenuItems>
      </UserButton>
    </div>
  )
}
