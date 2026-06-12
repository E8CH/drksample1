"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { login } from "@/components/actions/login-action";
import { useActionState } from "react";
import { SubmitButton } from "@/components/ui/submitButton";

export default function Page() {
  const [state, dispatch] = useActionState(login, undefined);
  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 px-4">
      <form action={dispatch}>
        <Card className="w-full max-w-sm rounded-lg shadow-lg border border-gray-300 bg-white">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-semibold text-gray-800">
              다락 관리자 로그인
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-6 p-6">
            <div className="grid gap-3">
              <Label htmlFor="username" className="text-gray-700">
                아이디
              </Label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                className="border-gray-300"
              />
              {state?.errors?.username && (
                <p className="text-sm text-red-500">{state.errors.username[0]}</p>
              )}
            </div>
            <div className="grid gap-3">
              <Label htmlFor="password" className="text-gray-700">
                비밀번호
              </Label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                className="border-gray-300"
              />
              {state?.errors?.password && (
                <p className="text-sm text-red-500">{state.errors.password[0]}</p>
              )}
            </div>
            {state?.server_validation_error && (
              <p className="text-sm text-red-500 text-center">
                {state.server_validation_error}
              </p>
            )}
            {state?.server_error && (
              <p className="text-sm text-red-500 text-center">
                {state.server_error}
              </p>
            )}
            <SubmitButton text="로그인" />
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
